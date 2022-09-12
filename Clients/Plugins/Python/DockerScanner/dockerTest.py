from main import DockerScanner



def test():
    ftp_check = DockerScanner("log4j", "-u http://192.168.27.6:8000/ --disable-tls-to-register-dns")
    res = ftp_check.execute("Apache")
    print(res)


test()    
    