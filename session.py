class Session:
    username = None
    id_user = None
    role = None
    dongle_key = None        # Kunci master AES dari flashdisk
    dongle_rahasia = None    # Alias kunci rahasia untuk enkripsi


current_session = Session()