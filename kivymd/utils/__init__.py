def ffloat(arg):
    try:
        return float(arg)
    except:
        return 0


def iffloat(arg):
    i = str(arg).find('.')
    if int(str(arg)[i+1:]) > 0:
        return arg
    return int(float(arg))
