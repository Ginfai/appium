def calculate_central_meridian(longitude):
    return (longitude+1.5)//3*3
def main():
    try:
        longitude=float(input("请输入经度:"))
        if(longitude<0 or longitude>180):
            print("经度值必须在0到180之间！")
            return
        result=calculate_central_meridian(longitude)
        print("3度带对应的中央经线为:",result)
    except ValueError:
        print("请输入正确的经度值!")

if __name__ == "__main__":
    main()    