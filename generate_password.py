import hashlib

password = input("insert password ->")
hashed_passwd = hashlib.md5(password.encode()).hexdigest()
print("the hashed password is:   "+str(hashed_passwd))
