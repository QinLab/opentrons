from labsuite.labware import containers, deck, pipettes
from labsuite.labware.grid import normalize_position
from labsuite.engine.context import Context
import labsuite.drivers.motor as motor_drivers
from labsuite.util.log import debug

import copy


class Protocol():

    _ingredients = None  # { 'name': "A1:A1" }

    _context = None  # Operational context (virtual robot).

    _instruments = None  # { 'A': instrument, 'B': instrument }

    _container_labels = None  # Aliases. { 'foo': (0,0), 'bar': (0,1) }

    _commands = None  # []

    _command_index = 0  # Index of the running command.

    _handlers = None  # List of attached handlers for run_next.

    def __init__(self):
        self._ingredients = {}
        self._container_labels = {}
        self._commands = []
        self._context = ContextHandler(self)
        self._handlers = []

    def add_container(self, slot, name, label=None):
        slot = normalize_position(slot)
        self._context.add_container(slot, name)
        if (label):
            label = label.lower()
            self._container_labels[label] = slot

    def add_instrument(self, slot, name):
        self._context.add_instrument(slot, name)

    def add_ingredient(self, name, location):
        pass

    def allocate(self, **kwargs):
        pass

    def calibrate(self, *args, **kwargs):
        self._context.calibrate(*args, **kwargs)

    def calibrate_instrument(self, axis, top=None, blowout=None, droptip=None):
        self._context.calibrate_instrument(
            axis, top=top, blowout=blowout, droptip=droptip
        )

    def transfer(self, start, end, ul=None, ml=None,
                 blowout=True, touchtip=True):
        if ul:
            volume = ul
        else:
            volume = ml * 1000

        self._commands.append({
            'transfer': {
                'tool': 'p10',
                'volume': volume,
                'start': self._normalize_address(start),
                'end': self._normalize_address(end),
                'blowout': blowout,
                'touchtip': touchtip
            }
        })

    def transfer_group(self, *wells, ul=None, ml=None, **defaults):
        if ul:
            volume = ul
        elif ml:
            volume = ul * 1000
        else:
            volume = None
        defaults.update({
            'touchtip': True,
            'blowout': True,
            'volume': volume
        })
        transfers = []
        for item in wells:
            options = defaults.copy()
            if len(item) is 3:
                start, end, opts = item
                options.update(opts)
            else:
                start, end = item
            vol = options.get('ul') or options.get('ml', 0) * 1000
            vol = vol or volume
            transfers.append({
                'volume': vol,
                'start': self._normalize_address(start),
                'end': self._normalize_address(end),
                'blowout': options['blowout'],
                'touchtip': options['touchtip']
            })
        self._commands.append({
            'transfer_group': {
                'tool': 'p10',
                'transfers': transfers
            }
        })

    def distribute(self, start, *wells, blowout=True):
        transfers = []
        for item in wells:
            end, volume = item
            transfers.append({
                'volume': volume,
                'end': self._normalize_address(end)
            })
        self._commands.append({'distribute': {
            'tool': 'p10',
            'start': self._normalize_address(start),
            'blowout': blowout,
            'transfers': transfers
        }})

    def consolidate(self, end, *wells, blowout=True):
        transfers = []
        for item in wells:
            start, volume = item
            transfers.append({
                'volume': volume,
                'start': self._normalize_address(start)
            })
        self._commands.append({'consolidate': {
            'tool': 'p10',
            'end': self._normalize_address(end),
            'blowout': blowout,
            'transfers': transfers
        }})

    def mix(self, start, volume=None, repetitions=None, blowout=True):
        self._commands.append({'mix': {
            'tool': 'p10',
            'start': self._normalize_address(start),
            'blowout': blowout,
            'volume': volume,
            'reps': repetitions
        }})

    @property
    def actions(self):
        return copy.deepcopy(self._commands)

    def _get_slot(self, name):
        """
        Returns a container within a given slot, can take a slot position
        as a tuple (0, 0) or as a user-friendly name ('A1') or as a label
        ('ingredients').
        """
        slot = None

        try:
            slot = normalize_position(name)
        except TypeError:
            if slot in self._container_labels:
                slot = self._container_labels[slot]

        if not slot:
            raise KeyError("Slot not defined: " + name)
        if slot not in self._deck:
            raise KeyError("Nothing in slot: " + name)

        return self._deck[slot]

    def _normalize_address(self, address):
        """
        Takes an address like "A1:A1" or "Ingredients:A1" and returns a tuple
        like (0, 0) or ('ingredients', 0).

        Container labels are retained in the address tuples so that named
        containers can be assigned to different slots within the user
        interface.
        """

        if ':' not in address:
            raise ValueError(
                "Address must be in the form of 'container:well'."
            )

        container, well = address.split(':')
        well = normalize_position(well)

        try:
            container = normalize_position(container)
        except ValueError:
            container = container.lower()
            if container not in self._container_labels:
                raise KeyError("Container not found: {}".format(container))

        return (container, well)

    def run_next(self):
        i = self._command_index
        next_command = self._commands[self._command_index]
        cur = self._commands[i]
        command = list(cur)[0]
        args = cur[command]
        debug("Protocol", "Running {} with args: {}".format(command, args))
        self._run(command, args)
        self._command_index += 1

    def _run(self, command, kwargs):
        method = getattr(self._context, command)
        if not method:
            raise KeyError("Command not defined: " + command)
        method(**kwargs)
        for h in self._handlers:
            method = getattr(h, command)
            method(**kwargs)

    def attach_handler(self, handler_class):
        """
        When you attach a handler, commands are run on the handler in sequence
        when Protocol.run_next() is called.

        You don't have to attach the ContextHandler, you get that for free.
        It's a good example implementation of what these things are
        supposed to do.

        Any command that the robot supports must be present on the Handler
        you pass in, or you'll get exceptions. Just make sure you subclass
        from ProtocolHandler and you'll be fine; empty methods are stubbed
        out for all supported commands.

        Pass in the class, not an instance. This method returns the
        instantiated object, which you can use to do any additional setup
        required for the particular Handler.
        """
        handler = handler_class(self, self._context)
        self._handlers.append(handler)
        return handler


class ProtocolHandler():

    """
    Empty interface that all ProtocolHandlers should support.  If a command
    isn't officially supported, it'll just be silently ignored.

    Normalization doesn't happen here. Don't call these classes directly,
    let the Protocol do its work first and run things internally.

    Do not do validation in these handlers. Don't do it.

    Use Protocol.attach to attach a handler.
    """

    _context = None
    _protocol = None  # Don't touch the protocol, generally.

    def __init__(self, protocol, context=None):
        self._context = context
        self._protocol = protocol
        self.setup()

    def setup(self):
        """
        Whatever setup you need to do for your context, do it here.
        """
        pass

    def transfer(self, start=None, end=None, volume=None, **kwargs):
        pass

    def transfer_group(self, *transfers):
        pass

    def distribute(self):
        pass

    def mix(self):
        pass

    def consolidate(self):
        pass


class ContextHandler(ProtocolHandler):

    """
    ContextHandler runs all the stuff on the virtual robot in the background
    and makes relevant data available.
    """

    _deck = None
    _instruments = None  # Axis as keys; Pipette object as vals.

    def setup(self):
        self._deck = deck.Deck()
        self._instruments = {}

    def add_instrument(self, axis, name):
        # We only have pipettes now so this is pipette-specific.
        self._instruments[axis] = pipettes.load_instrument(name)

    def get_instrument(self, axis=None, volume=None):
        if axis:
            if axis not in self._instruments:
                raise KeyError(
                    "No instrument assigned to {} axis.".format(axis)
                )
            else:
                return self._instruments[axis]
        if volume:
            for k, i in self._instruments.items():
                if i.supports_volume(volume):
                    return i

        raise KeyError(
            "No instrument found to support a volume of {}µl."
            .format(volume)
        )

    def calibrate_instrument(self, axis, top=None, blowout=None, droptip=None):
        kwargs = {'top': top, 'blowout': blowout, 'droptip': droptip,
                  'axis': axis}
        self.get_instrument(axis=axis).calibrate(**kwargs)

    def add_container(self, slot, container_name):
        self._deck.add_module(slot, container_name)

    def calibrate(self, slot, x=None, y=None, z=None):
        self._deck.calibrate(**{slot: {'x': x, 'y': y, 'z': z}})

    def get_coordinates(self, position):
        """ Returns the calibrated coordinates for a position. """
        slot, well = position
        return self._deck.slot(slot).well(well).coordinates()

    def get_volume(self, well):
        slot, well = self._protocol._normalize_address(well)
        return self._deck.slot(slot).well(well).get_volume()

    def get_tip_coordinates(self, size):
        """
        Returns the coordinates of the next available pipette tip for that
        particular size (ie, p10).
        """
        pass

    def transfer(self, start=None, end=None, volume=None, **kwargs):
        start_slot, start_well = start
        end_slot, end_well = end
        start = self._deck.slot(start_slot).well(start_well)
        end = self._deck.slot(end_slot).well(end_well)
        start.transfer(volume, end)

    def transfer_group(self, *transfers):
        pass

    def distribute(self):
        pass

    def mix(self):
        pass

    def consolidate(self):
        pass


class MotorControlHandler(ProtocolHandler):

    _driver = None
    _pipette_motors = None  # {axis: PipetteMotor}

    def set_driver(self, connection):
        self._driver = connection
        self._pipette_motors = {}

    def connect(self, port):
        self._driver.connect(device=port)

    def transfer(self, start=None, end=None, volume=None, **kwargs):
        self.move_volume(start, end, volume)

    def move_volume(self, start, end, volume):
        pipette = self.get_pipette(volume=volume)
        self.move_to_well(start)
        pipette.plunge(volume)
        self.move_into_well(start)
        pipette.release()
        self.move_to_well(end)
        self.move_into_well(end)
        pipette.blowout()
        self.move_up()
        pipette.release()

    def pickup_tip(self):
        pass

    def dispose_tip(self):
        pass

    def move_to_well(self, well):
        self.move_motors(z=0)  # Move up so we don't hit things.
        coords = self._context.get_coordinates(well)
        x, y, z = coords
        self.move_motors(x=x, y=y)
        self.move_motors(z=z)

    def move_into_well(self, well):
        x, y, z = self._context.get_coordinates(well)
        z = z + 10
        self.move_motors(x=x, y=y, z=z)

    def move_up(self):
        self.move_motors(z=0)

    def depress_plunger(self, volume):
        axis, depth = self._context.get_plunge(volume=volume)
        self.move_motors(**{axis: depth})

    def get_pipette(self, volume=None, axis=None):
        """
        Returns a closure object that allows for the plunge, release, and
        blowout of a certain pipette and volume.
        """
        pipette = self._context.get_instrument(volume=volume, axis=axis)
        axis = pipette.axis
        if axis not in self._pipette_motors:
            self._pipette_motors[axis] = PipetteMotor(pipette, self)
        return self._pipette_motors[axis]

    def move_motors(self, **kwargs):
        debug("MotorHandler", "Moving: {}".format(kwargs))
        self._driver.move(**kwargs)


class PipetteMotor():

        def __init__(self, pipette, motor):
            self.pipette = pipette
            self.motor = motor

        def plunge(self, volume):
            depth = self.pipette.plunge_depth(volume)
            self.move(depth)

        def release(self):
            self.move(0)

        def blowout(self):
            self.move(self.pipette.blowout)

        def move(self, position):
            axis = self.axis
            self.motor.move_motors(**{axis: position})

        @property
        def axis(self):
            return self.pipette.axis