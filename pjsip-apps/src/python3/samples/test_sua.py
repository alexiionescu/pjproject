from pathlib import Path
import shlex
import threading
import pjsua as pj

# Logging callback
def log_cb(level, msg, len):
    print(msg)


class MyAccountCallback(pj.AccountCallback):
    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)
        self.busy = False

    # Notification on incoming call
    def on_incoming_call(self, call):
        print(self.account.info().uri, "Incoming call from ", call.info().remote_uri)
        call.set_callback(MyCallCallback(call, self))
        call.answer(200)
        self.busy = True

    def on_reg_state(self):
        if self.account.info().reg_status >= 200:
            print(self.account.info().uri, "Registered Succesfull")


class MyAccountsCB:
    def __init__(self):
        self.accs_cb: list[MyAccountCallback] = []

    def __iadd__(self, acc_cb: MyAccountCallback):
        self.accs_cb.append(acc_cb)
        return self

    def __len__(self):
        return len(self.accs_cb)

    def GetAvailableAccount(self):
        for acc_cb in self.accs_cb:
            if acc_cb.busy == False:
                return acc_cb


# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None, acc_cb=None):
        pj.CallCallback.__init__(self, call)
        self.acc_cb = acc_cb

    def CallInfo(self):
        return (
            self.acc_cb.account.info().uri + " Call with " + self.call.info().remote_uri
        )

    # Notification when call state has changed
    def on_state(self):
        print(
            self.CallInfo(),
            self.call.info().state_text,
            "last code =",
            self.call.info().last_code,
            "reason =",
            self.call.info().last_reason,
        )

    # Notification when call's media state has changed.
    def on_media_state(self):
        global lib
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            lib.conf_connect(call_slot, 0)
            lib.conf_connect(0, call_slot)
            print(
                self.CallInfo(),
                "active media",
            )
        elif self.call.info().media_state == pj.MediaState.LOCAL_HOLD:
            print(
                self.CallInfo(),
                "local hold",
            )
        elif self.call.info().media_state == pj.MediaState.REMOTE_HOLD:
            print(
                self.CallInfo(),
                "remote hold",
            )

    def on_dtmf_digit(self, digits):
        print(
            self.CallInfo(),
            "digits:",
            digits,
        )


try:
    # Create library instance
    lib = pj.Lib()
    # pj.enable_trace = True

    # Init library with default config
    lib.init(log_cfg=pj.LogConfig(level=3, callback=log_cb))

    # Create UDP transport which listens to any available port
    transport = lib.create_transport(pj.TransportType.UDP)
    print("Listening on", transport.info().host, "port", transport.info().port)

    # Start the library
    lib.start()
    lib.set_null_snd_dev()
    accounts_cb = MyAccountsCB()

    # Wait for ENTER before quitting
    while True:
        command = shlex.split(input("Enter command (q to exit)>"))
        if command:
            if command[0] == "q":
                break
            elif command[0] == "call":
                acc_cb = accounts_cb.GetAvailableAccount()
                if acc_cb:
                    call = acc_cb.make_call(command[1])
                    call_cb = MyCallCallback(call, acc_cb)
                    call.set_callback(call_cb)
            elif command[0] == "add_acc":
                newacc = None
                if len(command) > 2:
                    accCfg = pj.AccountConfig(
                        command[0],
                        command[1],
                        registrar=len(command) > 3 and ("sip:" + command[3]) or "",
                        login=len(command) > 4 and command[4] or "",
                        password=len(command) > 5 and command[5] or "",
                        display="Python3Acc",
                    )
                    newacc = lib.create_account(accCfg)
                    acc_cb = MyAccountCallback(newacc)
                    newacc.set_callback(acc_cb)
                    acc_cb.wait()
                    accounts_cb += acc_cb
                elif len(accounts_cb) == 0:
                    # Create local/user-less account
                    newacc = lib.create_account_for_transport(transport)
                    acc_cb = MyAccountCallback(newacc)
                    newacc.set_callback(acc_cb)
                    accounts_cb += acc_cb
            elif command[0] == "load_accs":
                cfgfn = (
                    len(command) > 1
                    and Path(command[1])
                    or (Path.home() / ".pjsua/accounts_cfg.py")
                )
                with cfgfn.open() as f:
                    accountsInfo = eval(f.read())
                for acci in accountsInfo:
                    accCfg = pj.AccountConfig(
                        str(acci[0]),
                        str(acci[1]),
                        registrar=("sip:" + str(acci[2])),
                        login=str(acci[3]),
                        password=str(acci[4]),
                        display="Python3Acc",
                    )
                    newacc = lib.create_account(accCfg)
                    acc_cb = MyAccountCallback(newacc)
                    newacc.set_callback(acc_cb)
                    accounts_cb += acc_cb

    # We're done, shutdown the library
    lib.destroy()
    del lib

except pj.Error as e:
    print("Exception:", e)
    lib.destroy()
    del lib
except KeyboardInterrupt:
    print("Ctrl+C Received")
    lib.destroy()
    del lib
