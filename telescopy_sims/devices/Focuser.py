import threading
import time

from indi.device import Driver
from indi.device.pool import DevicePool
from indi.device import properties
from indi.message import const


@DevicePool.register
class Focuser(Driver):
    name = 'FOCUSER_SIMULATOR'

    general = properties.Group(
        'GENERAL',
        vectors=dict(
            connection=properties.Standard('CONNECTION', onchange='connect'),
            info=properties.TextVector(
                'INFO',
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    manufacturer=properties.Text('MANUFACTURER', default='Wiktor Latanowicz'),
                    camera_model=properties.Text('FOCUSER_MODEL', default='FocuserSimulator'),
                )
            ),
            active_device=properties.Standard(
                'ACTIVE_DEVICES',
                elements=dict(
                    camera=properties.Text('ACTIVE_FOCUSER', default=name)
                )
            )
        )
    )

    position = properties.Group(
        'POSITION',
        enabled=False,
        vectors=dict(
            position=properties.Standard('ABS_FOCUS_POSITION'),
        )
    )

    position.position.position.onwrite = 'reposition'

    def connect(self, sender):
        connected = self.general.connection.connect.bool_value
        self.position.enabled = connected
        self.general.info.enabled = connected

    def reposition(self, sender, value):
        def worker():
            step_size = 85
            delay = 1

            self.position.position.state_ = const.State.BUSY
            diff = float(value) - sender.value
            while abs(diff) > 0.1:
                dir = 1 if diff > 0 else -1
                step = dir * min(step_size, abs(diff))
                time.sleep(delay)
                sender.value = sender.value + step
                diff = float(value) - sender.value
            self.position.position.state_ = const.State.OK

        w = threading.Thread(target=worker, daemon=True)
        w.start()
