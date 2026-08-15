import pytest
from datetime import datetime, timedelta
from app.crud import otp as crud_otp
from app.schemas.otp import OTPVerificationCreate
from app.services import auth_service

def test_otp_lifecycle_sliding_grace_and_cooldown(db_session):
    test_email = "test_qa_otp@example.com"
    
    # Clean prior test state
    crud_otp.delete_otp(db_session, test_email)
    
    # 1. First OTP generation -> returns 60s cooldown
    eligible, wait_sec, cooldown = crud_otp.check_resend_eligibility(db_session, test_email)
    assert eligible is True
    assert cooldown == 60
    
    code1 = auth_service.generate_otp_code()
    otp_in1 = OTPVerificationCreate(
        email=test_email,
        otp_code=auth_service.get_otp_hash(code1),
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db_otp1, next_cd1 = crud_otp.create_otp(db_session, otp_in1)
    assert next_cd1 == 60
    
    # 2. Immediate resend attempt -> blocked by 60s cooldown
    eligible, wait_sec, _ = crud_otp.check_resend_eligibility(db_session, test_email)
    assert eligible is False
    assert wait_sec > 0
    
    # 3. Simulate 61 seconds elapsed -> eligible for 2nd resend (tier 2: 180s / 3 mins)
    db_otp1.created_at = datetime.utcnow() - timedelta(seconds=61)
    db_session.commit()
    
    eligible, wait_sec, cooldown2 = crud_otp.check_resend_eligibility(db_session, test_email)
    assert eligible is True
    assert cooldown2 == 180
    
    code2 = auth_service.generate_otp_code()
    otp_in2 = OTPVerificationCreate(
        email=test_email,
        otp_code=auth_service.get_otp_hash(code2),
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db_otp2, next_cd2 = crud_otp.create_otp(db_session, otp_in2)
    assert next_cd2 == 180
    
    # 4. Verify sliding grace window: Both code1 and code2 are active
    active_codes = crud_otp.get_active_otps(db_session, test_email)
    assert len(active_codes) == 2
    
    # 5. Test wrong code attempt -> returns attempts remaining
    res_wrong = auth_service.validate_otp(db_session, test_email, "000000")
    assert res_wrong["status"] == "INVALID"
    assert res_wrong["attempts_left"] < 5
    
    # 6. Test entering the EARLIER code (code1) -> succeeds due to grace window
    res_success = auth_service.validate_otp(db_session, test_email, code1)
    assert res_success["status"] == "SUCCESS"
    
    # 7. Check that all codes are now invalidated
    active_after = crud_otp.get_active_otps(db_session, test_email)
    assert len(active_after) == 0
    assert crud_otp.is_email_verified(db_session, test_email) is True
    
    # Cleanup
    crud_otp.delete_otp(db_session, test_email)
