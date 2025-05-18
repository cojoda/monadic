from monadic.session_manager import Session




if __name__ == '__main__':
    
    session = Session([])
    result  = session.exchange('test')

    print(result)
