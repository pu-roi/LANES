"""Scheduling inputs remain distinct from current street-flood evidence."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.services.news_weather_service import POINTS, choose_interval, parse_open_meteo, parse_pagasa, fetch_weather
from app.schemas.news_weather import WeatherProvider
from app.core import news_scheduler_auth as auth

NOW = datetime(2026, 10, 11, 13, 30, tzinfo=timezone.utc)


def provider(name, status="quiet", age=0):
    return WeatherProvider(name=name, status=status, checked_at=NOW-timedelta(minutes=age), source_url="https://example.invalid")


@pytest.mark.parametrize("statuses,expected", [(("quiet","quiet"),60), (("risk","unavailable"),15),
    (("uncertain","risk"),15), (("quiet","unavailable"),30), (("uncertain","quiet"),30), (("unavailable","unavailable"),30)])
def test_policy_risk_precedence_and_both_sources_required(statuses, expected):
    assert choose_interval([provider(name, status) for name,status in zip(("Open-Meteo","PAGASA"), statuses)], now=NOW).interval_minutes == expected


@pytest.mark.parametrize("age,expected", [(29,60), (30,30), (31,30), (-1,30)])
def test_snapshot_age(age, expected):
    assert choose_interval([provider("Open-Meteo",age=age),provider("PAGASA",age=age)],now=NOW).interval_minutes == expected


@pytest.mark.parametrize("minutes,expected", [(0,15),(59,15),(60,60),(61,60)])
def test_cooldown_does_not_extend_without_positive_signal(minutes, expected):
    result = choose_interval([provider("Open-Meteo"),provider("PAGASA")],now=NOW,last_positive_at=NOW-timedelta(minutes=minutes))
    assert result.interval_minutes == expected
    assert result.last_positive_at == NOW-timedelta(minutes=minutes)


def test_current_flood_overrides_weather_failure():
    assert choose_interval([], now=NOW, active_flood=True).interval_minutes == 15


def meteo(amount=0):
    return [{"latitude":p.latitude,"longitude":p.longitude,"utc_offset_seconds":0,"hourly_units":{"precipitation":"mm"},
             "hourly":{"time":["2026-10-11T13:00","2026-10-11T14:00","2026-10-11T15:00"],"precipitation":[amount,0,0]}} for p in POINTS]


@pytest.mark.parametrize("amount,status", [(0,"quiet"),(.199,"quiet"),(.2,"risk"),(.201,"risk"),(None,"uncertain"),(True,"uncertain"),(float("nan"),"uncertain"),(-1,"uncertain")])
def test_precipitation_threshold_and_invalid_values(amount,status):
    assert parse_open_meteo(meteo(amount),now=NOW).status == status


def test_upstream_only_and_partial_positive_signal():
    payload=meteo()
    payload[-1]["hourly"]["precipitation"][1]=.2
    payload[0]["hourly"]["precipitation"][0]=None
    result=parse_open_meteo(payload,now=NOW)
    assert result.status=="risk" and result.risk_locations==["Antipolo"]
    assert result.error_code=="weather_coverage_incomplete"


@pytest.mark.parametrize("change", ["missing_point","missing_slot","wrong_coordinate","wrong_units","duplicate_slot"])
def test_meteo_coverage_cannot_be_assumed(change):
    payload=meteo()
    if change=="missing_point": payload.pop()
    if change=="missing_slot": payload[0]["hourly"]["time"][1]="2026-10-12T14:00"
    if change=="wrong_coordinate": payload[0]["latitude"]=0
    if change=="wrong_units": payload[0]["hourly_units"]["precipitation"]="inch"
    if change=="duplicate_slot": payload[0]["hourly"]["time"][1]=payload[0]["hourly"]["time"][0]
    assert parse_open_meteo(payload,now=NOW).status=="uncertain"


def pagasa(rain, thunder="As of today, there is no Thunderstorm Advisory Issued."):
    return f'<div>Unrelated forecast Metro Manila</div><div id="rainfalls"><div>{rain}</div></div><div id="thunderstorms"><div>{thunder}</div></div>'


def bulletin(location="Metro Manila", clock="8:00 PM, 11 October 2026", suffix=""):
    return f"Rainfall Advisory No. 6 #NCR_PRSD<br>Issued at: {clock}(Sunday)<br>Rains affecting {location}.<br>{suffix}"


def test_real_page_shape_and_positive_precedence_over_undated_no_warning():
    result=parse_pagasa(pagasa(bulletin()),now=NOW)
    assert result.status=="risk" and result.error_code=="advisory_timestamp_missing"
    assert result.bulletins[0].issued_at==NOW-timedelta(minutes=90)
    assert result.bulletins[0].relevant


@pytest.mark.parametrize("location,status", [("Cavite","uncertain"),("Rizal","risk"),("Metro Manila","risk"),("NCR","risk"),("Quezon City","risk"),("San Mateo","risk"),("Las Pinas","risk"),("Antipolo","risk")])
def test_pagasa_geography(location,status):
    assert parse_pagasa(pagasa(bulletin(location)),now=NOW).status==status


def test_pagasa_compact_midnight_clock():
    result=parse_pagasa(pagasa(bulletin(suffix="The next advisory will be issued at 12:00AM tomorrow.")),now=NOW)
    assert result.status=="risk"
    assert result.bulletins[0].valid_until==datetime(2026,10,11,16,tzinfo=timezone.utc)


@pytest.mark.parametrize("clock", ["4:00 PM, 11 October 2026", "8:00 PM, 10 October 2026", "10:00 PM, 11 October 2026", "bad timestamp"])
def test_stale_future_and_malformed_bulletins_are_not_positive(clock):
    assert parse_pagasa(pagasa(bulletin(clock=clock)),now=NOW).status=="uncertain"


def test_midnight_next_warning_and_explicit_expiry():
    late=NOW.replace(hour=15,minute=30)  # 11:30 PM PHT
    text=bulletin(clock="11:00 PM, 11 October 2026",suffix="Watch for the next warning to be issued at 2:00 AM tomorrow.")
    result=parse_pagasa(pagasa(text),now=late)
    assert result.bulletins[0].valid_until==datetime(2026,10,11,18,tzinfo=timezone.utc)
    text=bulletin(suffix="Valid until: 9:00 PM, 11 October 2026")
    result=parse_pagasa(pagasa(text),now=NOW)
    assert choose_interval([provider("Open-Meteo"),result],now=NOW+timedelta(minutes=30)).interval_minutes==30


def test_expired_advisory_no_longer_refreshes_risk_even_with_fresh_fetch():
    result=parse_pagasa(pagasa(bulletin(suffix="Valid until: 9:35 PM, 11 October 2026")),now=NOW)
    assert choose_interval([provider("Open-Meteo"),result],now=NOW+timedelta(minutes=6)).interval_minutes==30


def test_dated_clear_messages_support_quiet_and_tabs_scripts_are_ignored():
    no_rain="No Rainfall Advisory Issued.<br>Issued at: 8:00 PM, 11 October 2026"
    no_thunder="No Thunderstorm Advisory Issued.<br>Issued at: 8:00 PM, 11 October 2026"
    html=pagasa(no_rain,no_thunder)+"<script>Rainfall Advisory Metro Manila</script><!-- Rainfall Warning -->"
    assert parse_pagasa(html,now=NOW).status=="quiet"


def test_bounded_fetch_does_not_reuse_widget_cache():
    requests=[]
    def serve(request):
        requests.append(request)
        return httpx.Response(200,json=meteo()) if "open-meteo" in request.url.host else httpx.Response(200,text=pagasa(bulletin()))
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        assert [p.status for p in fetch_weather(client,now=NOW)]==["quiet","risk"]
    assert requests[0].url.params["forecast_hours"]=="3"
    assert len(requests[0].url.params["latitude"].split(","))==20
    assert all(request.headers["cache-control"]=="no-cache" for request in requests)


@pytest.mark.parametrize("status", [403,429,500])
def test_provider_failure_is_visible(status):
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(status))) as client:
        result=fetch_weather(client,now=NOW)
    assert all(p.status=="unavailable" and p.error_code for p in result)


def test_catalog_covers_seventeen_lgus_and_three_upstream_samples():
    assert len({p.locality for p in POINTS if p.role=="metro"})==17
    assert {p.locality for p in POINTS if p.role=="upstream"}=={"Antipolo","Rodriguez","San Mateo"}
    assert all(14.3 < p.latitude < 14.9 and 120.8 < p.longitude < 121.4 for p in POINTS)


@pytest.mark.parametrize("changes,expected", [({},None),({"email":"wrong@example.invalid"},403),({"iss":"evil"},403),({"email_verified":False},403)])
def test_oidc_exact_identity(monkeypatch,changes,expected):
    monkeypatch.setattr(auth.settings,"NEWS_SCHEDULER_AUDIENCE","https://api.example.invalid")
    monkeypatch.setattr(auth.settings,"NEWS_SCHEDULER_SERVICE_ACCOUNT","scheduler@example.invalid")
    payload={"iss":"https://accounts.google.com","email":"scheduler@example.invalid","email_verified":True,**changes}
    def verify(token,request,audience):
        assert audience=="https://api.example.invalid"
        return payload
    monkeypatch.setattr(auth.id_token,"verify_oauth2_token",verify)
    credentials=HTTPAuthorizationCredentials(scheme="Bearer",credentials="fixture")
    if expected:
        with pytest.raises(HTTPException) as error:auth.require_news_scheduler(credentials)
        assert error.value.status_code==expected
    else:
        assert auth.require_news_scheduler(credentials)==payload


def test_missing_and_application_token_denied(monkeypatch):
    with pytest.raises(HTTPException) as error: auth.require_news_scheduler(None)
    assert error.value.status_code==401
    monkeypatch.setattr(auth.settings,"NEWS_SCHEDULER_AUDIENCE","https://api.example.invalid")
    monkeypatch.setattr(auth.settings,"NEWS_SCHEDULER_SERVICE_ACCOUNT","scheduler@example.invalid")
    monkeypatch.setattr(auth.id_token,"verify_oauth2_token",lambda *a: (_ for _ in ()).throw(ValueError("invalid_signature")))
    with pytest.raises(HTTPException) as error:
        auth.require_news_scheduler(HTTPAuthorizationCredentials(scheme="Bearer",credentials="user-jwt"))
    assert error.value.status_code==401


@pytest.mark.asyncio
async def test_machine_endpoint_rejects_browser_jwt_before_dispatch(monkeypatch):
    from app.main import app
    from app.api.v1.endpoints import news_scheduler
    monkeypatch.setattr(auth.settings,"NEWS_SCHEDULER_AUDIENCE","https://api.example.invalid")
    monkeypatch.setattr(auth.settings,"NEWS_SCHEDULER_SERVICE_ACCOUNT","scheduler@example.invalid")
    monkeypatch.setattr(auth.id_token,"verify_oauth2_token",lambda *a: (_ for _ in ()).throw(ValueError("invalid_signature")))
    monkeypatch.setattr(news_scheduler,"run_weather_tick",lambda *a: (_ for _ in ()).throw(AssertionError("must not dispatch")))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://fixture") as client:
        assert (await client.post("/api/v1/internal/news-scheduler/tick")).status_code==401
        assert (await client.post("/api/v1/internal/news-scheduler/tick",headers={"Authorization":"Bearer browser-jwt"})).status_code==401


def test_cloud_run_submission_and_reconciliation(monkeypatch):
    from app.services import news_job_dispatch_service as dispatch
    monkeypatch.setattr(dispatch.google.auth,"default",lambda **kw:(SimpleNamespace(token="fixture",valid=True,refresh=lambda request:None),"fixture"))
    job="projects/fixture/locations/asia-east1/jobs/news"
    operation="projects/fixture/locations/asia-east1/operations/fixture"
    calls=[]
    def serve(request):
        calls.append(request)
        if request.method=="POST":return httpx.Response(200,json={"name":operation})
        if "operations" in request.url.path:return httpx.Response(200,json={"done":True,"response":{"name":job+"/executions/one"}})
        return httpx.Response(200,json={"name":job+"/executions/one","completionTime":"2026-10-11T13:40:00Z","failedCount":0})
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        gateway=dispatch.NewsJobGateway(job,client)
        assert gateway.start("reservation-one")==operation
        assert gateway.reconcile("reservation-one",operation,NOW)=="finished"
    import json
    assert json.loads(calls[0].content)["overrides"]["containerOverrides"][0]["env"][0]["value"]=="reservation-one"


@pytest.mark.parametrize("completion,expected", [(None,"running"),("2026-10-11T13:40:00Z","failed")])
def test_uncertain_start_found_by_execution_token(monkeypatch,completion,expected):
    from app.services import news_job_dispatch_service as dispatch
    monkeypatch.setattr(dispatch.google.auth,"default",lambda **kw:(SimpleNamespace(token="fixture",valid=True,refresh=lambda request:None),"fixture"))
    result={"executions":[{"template":{"containers":[{"env":[{"name":"LANES_NEWS_DISPATCH_TOKEN","value":"one"}]}]},"completionTime":completion,"failedCount":1}]}
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=result))) as client:
        assert dispatch.NewsJobGateway("projects/fixture/locations/asia-east1/jobs/news",client).reconcile("one",None,NOW)==expected


def test_incomplete_execution_listing_cannot_establish_absence(monkeypatch):
    from app.services import news_job_dispatch_service as dispatch
    monkeypatch.setattr(dispatch.google.auth,"default",lambda **kw:(SimpleNamespace(token="fixture",valid=True,refresh=lambda request:None),"fixture"))
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={"nextPageToken":"more"}))) as client:
        assert dispatch.NewsJobGateway("projects/fixture/locations/asia-east1/jobs/news",client).reconcile("one",None,NOW)=="unknown"
