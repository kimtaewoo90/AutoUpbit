import pyupbit

class Connection:

    def ConnectToUpbit(self):
        # 객체생성(Upbit 연결)
        access = "frGzp5hUEaQBNQ1uuO60Dx3QGkSm5ugsEVdfrpnr"
        secret = "L4wHqPfrfc7x8NYWHaL8IoUxbV8MBuhoxZG2ZHJa"
        upbit = pyupbit.Upbit(access, secret)

        return upbit



