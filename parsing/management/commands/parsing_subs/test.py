def ph(a):
    print(a,"tt")


a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

while a:
    ph(a[:2])
    a = a[2:]
    print(a)
print("fin")
# print(a[:5])
# print(a[5:])
