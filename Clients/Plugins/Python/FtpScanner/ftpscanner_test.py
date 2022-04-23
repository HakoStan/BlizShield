from .main import FtpChecker



def test_ftp_public_true():
    ftp_check = FtpChecker('195.144.107.198', 'demo', 'password')
    res = ftp_check.execute()

def test_ftp_public_anonymous_true():
    ftp_check = FtpChecker('195.144.107.198')
    res = ftp_check.execute()

def test_ftp_public_anonymous_true():
    ftp_check = FtpChecker('128.148.32.111')
    res = ftp_check.execute()

