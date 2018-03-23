import threading
import datetime
import os
import time

from indi.device import Driver
from indi.device.pool import DevicePool
from indi.device import properties
from indi.message import const

from telescopy import settings

import telescopy_sims


@DevicePool.register
class Camera(Driver):
    name = 'CAMERA_SIMULATOR'

    FOCUSER = 'FOCUSER_SIMULATOR'
    MIN_FOCUS = 0
    MAX_FOCUS = 859

    general = properties.Group(
        'GENERAL',
        vectors=dict(
            connection=properties.Standard('CONNECTION', onchange='connect'),
            info=properties.TextVector(
                'INFO',
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    battery_level=properties.Text('BATTERY_LEVEL', default='50%'),
                    manufacturer=properties.Text('MANUFACTURER', default='Wiktor Latanowicz'),
                    camera_model=properties.Text('CAMERA_MODEL', default='Camera Simulator'),
                )
            ),
            active_device=properties.Standard(
                'ACTIVE_DEVICES',
                elements=dict(
                    camera=properties.Text('ACTIVE_CCD', default=name)
                )
            )
        )
    )

    settings = properties.Group(
        'SETTINGS',
        enabled=False,
        vectors=dict(
            upload_mode=properties.Standard('UPLOAD_MODE', default_on='UPLOAD_LOCAL'),
            iso=properties.SwitchVector(
                'ISO',
                rule=properties.SwitchVector.RULES.ONE_OF_MANY,
                default_on='100',
                elements=dict(
                    iso100=properties.Switch('100'),
                    iso200=properties.Switch('200'),
                    iso400=properties.Switch('400'),
                    iso800=properties.Switch('800'),
                    iso1600=properties.Switch('1600'),
                    iso3200=properties.Switch('3200'),
                )
            ),
            quality=properties.Standard('CCD_COMPRESSION')
        )
    )

    exposition = properties.Group(
        'EXPOSITION',
        enabled=False,
        vectors=dict(
            exposure=properties.Standard('CCD_EXPOSURE')
        )
    )
    exposition.exposure.time.onwrite = 'expose'

    images = properties.Group(
        'IMAGES',
        enabled=False,
        vectors=dict(
            last_url=properties.TextVector(
                'LAST_IMAGE_URL',
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    arw=properties.Text('RAW'),
                    jpg=properties.Text('JPEG'),
                )
            )
        )
    )

    def connect(self, sender, **kwargs):
        connected = self.general.connection.connect.bool_value
        self.general.info.enabled = connected
        self.exposition.enabled = connected
        self.settings.enabled = connected
        self.images.enabled = connected

    def expose(self, sender, **kwargs):
        def worker():
            self.exposition.exposure.state_ = const.State.BUSY
            file_name = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
            time.sleep(1)

            focus = DevicePool.get(self.FOCUSER).position.position.position.value
            focus = min(focus, self.MAX_FOCUS)
            focus = max(focus, self.MIN_FOCUS)

            file_path = os.path.join(
                telescopy_sims.__path__[0],
                'resources',
                'images',
                'focus-10' + str(int(focus)).zfill(3) + '.jpg'
            )

            with open(file_path, 'rb') as f:
                img = f.read()

            imgs = {
                'jpg': img
            }

            if self.settings.upload_mode.selected_value in ('UPLOAD_LOCAL', 'UPLOAD_BOTH',):
                save_dir = os.path.join(settings.PUB_DIR, self.name)
                if not os.path.exists(save_dir):
                    os.mkdir(save_dir)

                for ext, data in imgs.items():
                    rel_path = os.path.join(self.name, f'{file_name}.{ext}')
                    file_path = os.path.join(save_dir, f'{file_name}.{ext}')
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    with open(file_path, mode='wb') as f:
                        f.write(data)

                    getattr(self.images.last_url, ext).value = rel_path

            self.exposition.exposure.state_ = const.State.OK

        w = threading.Thread(target=worker, daemon=True)
        w.start()
