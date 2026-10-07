"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings, type SettingsConfiguration, type SystemSettings } from "@/features/admin/adminApi";
import { Button, Card, CardContent, CardHeader, CardTitle, Checkbox, NumberInput, Select, Tabs } from "@/shared/ui";
import { Activity, Clock, CloudRain, Newspaper, RefreshCw, Save, ShieldCheck, type LucideIcon } from "lucide-react";
import toast from "react-hot-toast";
import { ApiError } from "@/lib/apiClient";

const key = ["systemSettings"];
const describeError = (error: unknown) => error instanceof Error ? error.message : "Unable to save settings. Please retry.";
const showTime = (value: string | null) => value ? new Date(value).toLocaleString("en-PH", { timeZone: "Asia/Manila" }) : "No run recorded";
const readable = (value: string) => value.replaceAll("_", " ");

const sections = [
  { id: "flood-zones", label: "Flood zones", icon: CloudRain },
  { id: "evidence-expiry", label: "Evidence expiry", icon: Clock },
  { id: "citizen-approval", label: "Citizen approval", icon: ShieldCheck },
  { id: "news-automation", label: "News automation", icon: Newspaper },
  { id: "operational-status", label: "Operational status", icon: Activity },
];
const pageClassName = "mx-auto w-full max-w-[1600px] space-y-6 text-gray-900 pb-[calc(var(--bottom-nav-height,0px)+env(safe-area-inset-bottom))]";

function Section({ id, title, description, icon: Icon, active, children }: { id: string; title: string; description: string; icon: LucideIcon; active: boolean; children: ReactNode }) {
  return (
    <section id={id} data-settings-panel={id} hidden={!active} aria-labelledby={`${id}-title`} className="min-w-0">
      <Card className="h-full shadow-sm">
        <CardHeader className="space-y-2 px-4 py-4 sm:px-5">
          <CardTitle id={`${id}-title`} className="flex items-center gap-2 text-base">
            <Icon aria-hidden="true" className="h-4 w-4 shrink-0 text-blue-600" />{title}
          </CardTitle>
          <p className="text-sm leading-relaxed text-gray-500">{description}</p>
        </CardHeader>
        <CardContent className="space-y-5 p-4 sm:p-5">{children}</CardContent>
      </Card>
    </section>
  );
}

export default function SystemSettingsPage() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: key, queryFn: getSettings, refetchInterval: 30_000, retry: (count, error) => !(error instanceof ApiError && [401, 403].includes(error.status)) && count < 2 });
  const [editor, setEditor] = useState<{ draft: SystemSettings; baseline: SettingsConfiguration } | null>(null);
  const baseline = editor?.baseline || query.data;
  const draft = editor?.draft || query.data?.settings;
  const [notice, setNotice] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState(sections[0].id);
  const dirty = !!draft && !!baseline && JSON.stringify(draft) !== JSON.stringify(baseline.settings);
  const mutation = useMutation({ mutationFn: updateSettings,
    onSuccess: (result) => {
      client.setQueryData(key, result); setEditor(null);
      setNotice(null); toast.success("System settings saved");
    },
    onError: (error: unknown) => { setNotice(describeError(error)); toast.error("Settings were not saved"); if (error instanceof ApiError && error.status === 409) void query.refetch(); },
  });
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    const navigate = (event: MouseEvent) => {
      const anchor = (event.target as Element).closest("a[href]");
      if (anchor && !window.confirm("You have unsaved settings. Leave this page and discard the draft?")) { event.preventDefault(); event.stopPropagation(); }
    };
    window.addEventListener("beforeunload", warn);
    document.addEventListener("click", navigate, true);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", navigate, true); };
  }, [dirty]);

  if (query.isLoading || (!draft && !query.isError)) return <div className={pageClassName}><h1 className="text-2xl font-bold tracking-tight">System Settings</h1><Card className="shadow-sm"><CardContent role="status" className="flex items-center gap-2 py-10 text-sm text-gray-500"><RefreshCw aria-hidden="true" className="h-4 w-4 animate-spin motion-reduce:animate-none" />Loading System Settings…</CardContent></Card></div>;
  if (!draft || !baseline) return <div className={pageClassName}><h1 className="text-2xl font-bold tracking-tight">System Settings</h1><Card className="border-red-200 bg-red-50 shadow-sm"><CardContent role="alert" className="space-y-3 text-sm text-red-700"><p>{describeError(query.error)}</p><Button onClick={() => void query.refetch()}>Retry loading settings</Button></CardContent></Card></div>;
  const current = query.data || baseline;
  const disabled = !current.can_edit || mutation.isPending;
  const update = <K extends keyof SystemSettings>(field: K, value: SystemSettings[K]) => setEditor((previous) => ({ baseline: previous?.baseline || current, draft: { ...(previous?.draft || current.settings), [field]: value } }));
  const revert = () => { setEditor(null); setNotice(null); };
  const save = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Keep native input constraints effective across every mounted tab.
    // Reveal an invalid field before asking the browser to focus and explain it.
    const invalidField = event.currentTarget.querySelector<HTMLInputElement>("input:invalid");
    if (invalidField) {
      const panel = invalidField.closest<HTMLElement>("[data-settings-panel]");
      if (panel?.dataset.settingsPanel) setActiveSection(panel.dataset.settingsPanel);
      requestAnimationFrame(() => { invalidField.focus(); invalidField.reportValidity(); });
      return;
    }
    mutation.mutate({ revision: baseline.revision, settings: draft });
  };
  const numeric = (field: "staff_road_buffer_metres" | "news_unconfirmed_retention_hours" | "citizen_min_trust" | "citizen_min_accuracy" | "citizen_min_human_reviews", label: string, min: number, max: number) =>
    <NumberInput aria-label={label} label={label} value={draft[field]} min={min} max={max} step={field === "staff_road_buffer_metres" ? 0.5 : 1} required disabled={disabled} onChange={(event) => update(field, event.target.value === "" ? NaN : event.target.valueAsNumber)} />;
  const toggle = (field: "citizen_auto_approval_enabled" | "news_collection_enabled" | "news_processing_enabled" | "news_publication_enabled", label: string, explanation: string) =>
    <Checkbox label={label} description={explanation} checked={draft[field]} disabled={disabled} onChange={(event) => update(field, event.target.checked)} />;
  return <form onSubmit={save} noValidate className={pageClassName}>
    <header className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">System Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Configure flood evidence, citizen approval, and news automation. All times are Philippine time.</p>
      </div>
      <Button type="button" variant="outline" disabled={query.isFetching} onClick={() => void query.refetch()} className="shrink-0 gap-2">
        <RefreshCw aria-hidden="true" className={`h-4 w-4 ${query.isFetching ? "animate-spin motion-reduce:animate-none" : ""}`} />Refresh status
      </Button>
    </header>

    {!current.can_edit && <p role="status" className="rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-800">You have view-only access. A role with full Settings permission can save changes.</p>}
    {notice && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{notice}</p>}
    {query.isError && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">Operational status could not refresh. Your draft is preserved. <Button type="button" variant="ghost" size="sm" onClick={() => void query.refetch()}>Retry</Button></p>}
    {dirty && current.revision !== baseline.revision && <p role="alert" className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">Settings changed elsewhere. Your draft is preserved. Use Revert to load the latest configuration before editing again.</p>}

    <nav aria-label="Settings sections">
      <Tabs tabs={sections} activeTab={activeSection} onChange={setActiveSection} variant="underline" layoutId="system-settings-sections" className="w-full" />
    </nav>

    <Section id="flood-zones" active={activeSection === "flood-zones"} icon={CloudRain} title="Flood Zone Configuration" description="Defaults apply to future staff-created road zones. Existing zones keep their geometry.">
      <div className="grid items-start gap-6 sm:grid-cols-2">
        <div className="space-y-3">
          {numeric("staff_road_buffer_metres", "Staff road buffer (metres)", 1, 100)}
          <p className="text-xs text-gray-500">Allowed range: 1–100 metres.</p>
        </div>
        <div className="space-y-3 border-t border-gray-100 pt-4 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0">
          <dl className="text-sm">
            <dt className="font-medium text-gray-700">Automatic news road buffer</dt>
            <dd className="mt-1 text-xl font-semibold text-gray-900">{current.automatic_news_buffer_metres} <span className="text-sm font-normal text-gray-500">metres</span></dd>
          </dl>
          <p className="text-sm leading-relaxed text-gray-500">This fixed margin is a placement policy and cannot be edited here.</p>
        </div>
      </div>
    </Section>

    <Section id="evidence-expiry" active={activeSection === "evidence-expiry"} icon={Clock} title="Evidence Expiry by Depth" description="When evidence expires, current conditions become Unconfirmed. This does not establish clearance or predict when water will subside. Fresh, qualified observations can refresh their contribution.">
      <fieldset className="min-w-0 space-y-3">
        <legend className="text-sm font-semibold text-gray-900">Observation freshness</legend>
        <p className="text-xs text-gray-500">Each depth can retain evidence for 30–120 minutes.</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{current.depth_options.map(({ key: depth, label }) => <NumberInput key={depth} aria-label={`${label} expiry (minutes)`} label={`${label} expiry (minutes)`} min={30} max={120} step={1} required disabled={disabled} value={draft.evidence_expiry_minutes[depth]} onChange={(event) => update("evidence_expiry_minutes", { ...draft.evidence_expiry_minutes, [depth]: event.target.value === "" ? NaN : event.target.valueAsNumber })} />)}</div>
      </fieldset>
      <div className="grid items-start gap-4 border-t border-gray-100 pt-4 sm:grid-cols-2">
        {numeric("news_unconfirmed_retention_hours", "News retention after expiry (hours)", 1, 72)}
        <p className="text-sm leading-relaxed text-gray-500">Existing decisions retain their saved deadlines. Explicit staff-managed zone deadlines remain separate. Duration-model development is separate work.</p>
      </div>
    </Section>

    <Section id="citizen-approval" active={activeSection === "citizen-approval"} icon={ShieldCheck} title="Citizen Automatic Approval" description="These are eligibility rules, not confidence probabilities. Only documented human reviews count; automatic approvals do not increase reputation.">
      <div className="grid items-start gap-6 lg:grid-cols-3">
        {toggle("citizen_auto_approval_enabled", "Enable citizen automatic approval", "Agreeing reports can support an active verified zone. New zones require two qualifying independent reporters.")}
        <fieldset className="min-w-0 space-y-3 lg:col-span-2">
          <legend className="text-sm font-semibold text-gray-900">Reporter eligibility</legend>
          <div className="grid gap-4 sm:grid-cols-3">{numeric("citizen_min_trust", "Minimum trust (out of 100)", 0, 100)}{numeric("citizen_min_accuracy", "Minimum reviewed accuracy (%)", 0, 100)}{numeric("citizen_min_human_reviews", "Minimum human reviews", 1, 100)}</div>
        </fieldset>
      </div>
      <p className="border-t border-gray-100 pt-4 text-sm leading-relaxed text-gray-500">Observation time must be explicit and no more than 30 minutes old. Known depth, matching conditions and validated continuous road geometry are required. Conflicts, copied evidence and incomplete reports remain in review.</p>
    </Section>

    <Section id="news-automation" active={activeSection === "news-automation"} icon={Newspaper} title="News Automation" description="Pause stages independently. Saved evidence remains available; expiry and qualified clearance maintenance continue.">
      <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
        <fieldset className="min-w-0 space-y-5">
          <legend className="mb-3 text-sm font-semibold text-gray-900">Automation stages</legend>
          {toggle("news_collection_enabled", "Automatic RSS collection", "Gather articles from selected verified publishers.")}
          {toggle("news_processing_enabled", "Automatic NLP / NER processing", "Extract saved flood observations and run independent evidence evaluation.")}
          {toggle("news_publication_enabled", "Automatic publication and plotting", "Publish eligible alerts and activate qualified road zones.")}
        </fieldset>
        <div className="min-w-0 space-y-6 border-t border-gray-100 pt-5 lg:border-t-0 lg:pt-0">
          <Select label="Collection interval (minutes)" disabled={disabled} value={draft.news_collection_interval_minutes} onChange={(event) => update("news_collection_interval_minutes", Number(event.target.value))} options={[15, 30, 60].map((value) => ({ value, label: `${value} minutes` }))} />
          <fieldset className="min-w-0">
            <legend className="mb-3 text-sm font-semibold text-gray-900">Verified news publishers</legend>
            <div className="grid gap-4 sm:grid-cols-2">{current.source_options.map((source) => <Checkbox key={source.id} label={source.publisher} disabled={disabled} checked={draft.news_source_ids.includes(source.id)} onChange={(event) => update("news_source_ids", event.target.checked ? [...draft.news_source_ids, source.id] : draft.news_source_ids.filter((id) => id !== source.id))} />)}</div>
          </fieldset>
        </div>
      </div>
    </Section>

    <Section id="operational-status" active={activeSection === "operational-status"} icon={Activity} title="Operational Status" description="Persisted worker results are shown here. An enabled checkbox alone does not establish that the deployed worker is operating.">
      <dl className="grid gap-5 text-sm sm:grid-cols-2 xl:grid-cols-4">
        <div><dt className="text-gray-500">Latest worker attempt</dt><dd className="mt-1 font-medium text-gray-900">{showTime(current.runtime.last_started_at)}</dd></div>
        <div><dt className="text-gray-500">Latest successful worker run</dt><dd className="mt-1 font-medium text-gray-900">{showTime(current.runtime.last_successful_at)}</dd></div>
        <div><dt className="text-gray-500">Next collection due</dt><dd className="mt-1 font-medium text-gray-900">{current.runtime.next_collection_at ? showTime(current.runtime.next_collection_at) : "Not recorded / paused"}</dd></div>
        <div><dt className="text-gray-500">Worker state</dt><dd className="mt-1 font-medium text-gray-900">{current.runtime.running ? "Running" : current.runtime.error_code ? readable(current.runtime.error_code) : current.runtime.last_started_at ? "Idle / no failure recorded" : "No worker run recorded"}</dd></div>
      </dl>
      <dl className="flex flex-wrap gap-x-6 gap-y-2 border-t border-gray-100 pt-4 text-sm">
        {Object.entries(current.runtime.stage_outcomes).map(([stage, result]) => <div key={stage} className="flex flex-wrap gap-2"><dt className="capitalize text-gray-500">{readable(stage)}:</dt><dd className="font-medium capitalize text-gray-900">{readable(result)}</dd></div>)}
      </dl>
      <div className="grid gap-6 lg:grid-cols-3">
        {Object.entries(current.runtime.stages || {}).map(([stage, health]) => <div key={stage} className="min-w-0 space-y-3 border-t border-gray-100 pt-4 text-sm">
          <h3 className="font-semibold capitalize text-gray-900">{readable(stage)}: {readable(health.outcome)}</h3>
          <dl className="space-y-2 text-gray-600"><div><dt className="text-xs text-gray-500">Latest attempt</dt><dd>{showTime(health.last_attempt_at)}</dd></div><div><dt className="text-xs text-gray-500">Latest success</dt><dd>{showTime(health.last_success_at)}</dd></div></dl>
          <dl className="space-y-1">{Object.entries(health.counts).map(([name, count]) => <div key={name} className="flex justify-between gap-3"><dt className="text-gray-500">{readable(name)}</dt><dd className="font-medium tabular-nums text-gray-900">{count}</dd></div>)}</dl>
          {health.errors.length > 0 && <p role="alert" className="break-words text-red-700">{health.errors.map(readable).join(", ")}</p>}
          {stage === "collection" && health.outcome === "completed" && health.counts.eligible_candidates === 0 && <p className="text-gray-500">No eligible flood reports found in this collection run.</p>}
        </div>)}
      </div>
      <p className="text-xs leading-relaxed text-gray-500">Worker tick target: {current.runtime.scheduler_tick_minutes} minutes. Verify the matching deployment and Scheduler configuration when releasing these settings.</p>
    </Section>

    <footer className="sticky bottom-0 z-20 flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <p role="status" className={`text-sm ${dirty ? "font-medium text-amber-700" : "text-gray-500"}`}>{dirty ? "Unsaved changes" : `Saved configuration · revision ${baseline.revision}`}</p>
        <p className="text-xs text-gray-500">Save and Revert apply to all settings tabs.</p>
      </div>
      <div className="flex gap-3">
        <Button type="button" variant="outline" disabled={mutation.isPending || !dirty} onClick={revert} className="shrink-0">Revert</Button>
        <Button type="submit" disabled={disabled || !dirty || baseline.revision !== current.revision} className="min-w-0 flex-1 gap-2 whitespace-nowrap px-3 sm:flex-none sm:px-4"><Save aria-hidden="true" className="hidden h-4 w-4 sm:block" />{mutation.isPending ? "Saving…" : "Save settings"}</Button>
      </div>
    </footer>
  </form>;
}
