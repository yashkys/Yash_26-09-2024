from datetime import datetime

def infoLog(msg):
    return
    print(f"INFO : {datetime.now()} : {msg}")

    
def warningLog(msg):
    print(f"WARNING : {datetime.now()} : {msg}")

    
def errorLog(msg):
    print(f"ERROR : {datetime.now()} : {msg}")
    
    
def successLog(msg):
    return 
    print(f"SUCCESS : {datetime.now()} : {msg}")