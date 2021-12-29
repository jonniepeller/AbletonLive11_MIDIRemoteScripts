# -*- coding: utf-8 -*-

from _Framework.ModeSelectorComponent import ModeSelectorComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.SessionZoomingComponent import DeprecatedSessionZoomingComponent  # noqa
from .SpecialSessionComponent import SpecialSessionComponent
from .Settings import Settings


class MainSelectorComponent(ModeSelectorComponent):

    """Class that reassigns the button on the launchpad to different functions"""

    def __init__(
        self,
        matrix,
        top_buttons,
        side_buttons,
        config_button,
        control_surface,
    ):
        # verify matrix dimentions
        assert isinstance(matrix, ButtonMatrixElement)
        assert (matrix.width() == 8) and (matrix.height() == 8)
        assert isinstance(top_buttons, tuple)
        assert len(top_buttons) == 8
        assert isinstance(side_buttons, tuple)
        assert len(side_buttons) == 8
        assert isinstance(config_button, ButtonElement)
        ModeSelectorComponent.__init__(self)  # super constructor

        # inject ControlSurface
        self._matrix = matrix
        self._nav_buttons = top_buttons[:4]  # arrow buttons
        self._mode_buttons = top_buttons[4:]  # session,user1,user2,mixer buttons
        self._side_buttons = side_buttons  # launch buttons
        self._config_button = config_button  # used to reset launchpad
        self._control_surface = control_surface

        # initialize index variables
        self._mode_index = 0  # Inherited from parent
        self._main_mode_index = 0  # LP original modes
        self._sub_mode_list = [0, 0, 0, 0]
        for index in range(4):
            self._sub_mode_list[index] = 0
        self.set_mode_buttons(self._mode_buttons)

        ###SESSION COMPONENT
        self._session = SpecialSessionComponent(
            matrix.width(), matrix.height(), None, self._control_surface, self
        )

        # initialize _session variables
        self._session.name = "Session_Control"

        ###ZOOMING COMPONENT
        self._zooming = DeprecatedSessionZoomingComponent(
            self._session, enable_skinning=True
        )
        self._zooming.name = "Session_Overview"
        self._zooming.set_empty_value("Default.Button.Off")

        # Non-Matrix buttons
        self._all_buttons = []
        for button in self._side_buttons + self._nav_buttons:
            self._all_buttons.append(button)

        self._init_session()
        self._all_buttons = tuple(self._all_buttons)

    def disconnect(self):
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)

        self._session = None
        self._zooming = None
        for button in self._all_buttons:
            button.set_on_off_values("DefaultButton.Disabled", "DefaultButton.Disabled")

        self._config_button.turn_off()
        self._matrix = None
        self._side_buttons = None
        self._nav_buttons = None
        self._config_button = None
        ModeSelectorComponent.disconnect(self)

    def session_component(self):
        return self._session

    def _update_mode(self):
        mode = self._modes_heap[-1][
            0
        ]  # get first value of last _modes_heap tuple. _modes_heap tuple structure is (mode, sender, observer)

        # TODO Gut this
        assert mode in range(self.number_of_modes())  # 8 for this script
        if self._main_mode_index == mode:
            if (
                self._main_mode_index == 1
            ):  # user mode 1 and device controller and instrument mode
                self._sub_mode_list[self._main_mode_index] = (
                    self._sub_mode_list[self._main_mode_index] + 1
                ) % len(Settings.USER_MODES_1)
                self.update()
            elif self._main_mode_index == 2:  # user mode 2  and step sequencer
                self._sub_mode_list[self._main_mode_index] = (
                    self._sub_mode_list[self._main_mode_index] + 1
                ) % len(Settings.USER_MODES_2)
                self.update()
            elif self._main_mode_index == 3:  # Mixer mode
                self.update()
            else:  # Session mode
                self._sub_mode_list[self._main_mode_index] = 0
                self._mode_index = 0

        else:
            self._main_mode_index = mode
            self.update()

    def set_mode(self, mode):
        self._clean_heap()
        self._modes_heap = [(mode, None, None)]

    def number_of_modes(self):
        return 1 + 3 + 3 + 1

    def on_enabled_changed(self):
        self.update()

    def _update_mode_buttons(self):
        self._modes_buttons[0].set_on_off_values("Mode.Session.On", "Mode.Session.Off")
        self._modes_buttons[3].set_on_off_values("Mode.Mixer.On", "Mode.Mixer.Off")
        mode1 = self.getSkinName(Settings.USER_MODES_1[self._sub_mode_list[1]])
        mode2 = self.getSkinName(Settings.USER_MODES_2[self._sub_mode_list[2]])
        self._modes_buttons[1].set_on_off_values(
            "Mode." + mode1 + ".On", "Mode." + mode1 + ".Off"
        )
        self._modes_buttons[2].set_on_off_values(
            "Mode." + mode2 + ".On", "Mode." + mode2 + ".Off"
        )

        for index in range(4):
            if index == self._main_mode_index:
                self._modes_buttons[index].turn_on()
            else:
                self._modes_buttons[index].turn_off()

    def getSkinName(self, user2Mode):
        if user2Mode == "instrument":
            user2Mode = "Note"
        if user2Mode == "device":
            user2Mode = "Device"
        if user2Mode == "user 1":
            user2Mode = "User"
        if user2Mode == "user 2":
            user2Mode = "User2"
        if user2Mode == "drum stepseq":
            user2Mode = "StepSequencer"
        if user2Mode == "melodic stepseq":
            user2Mode = "StepSequencer2"
        return user2Mode

    def channel_for_current_mode(self):
        # in this code, midi channels start at 0.
        # so channels range from 0 - 15.
        # mapping to 1-16 in the real world

        if self._main_mode_index == 0:
            new_channel = 0  # session

        elif self._main_mode_index == 3:
            new_channel = 6  # mixer

        return new_channel

    def update(self):
        assert self._modes_buttons != None
        if self.is_enabled():

            self._update_mode_buttons()

            as_active = True
            as_enabled = True
            self._session.set_allow_update(False)
            self._zooming.set_allow_update(False)
            self._config_button.send_value(
                40
            )  # Set LP double buffering mode (investigate this)
            self._config_button.send_value(1)  # Set LP X-Y layout grid mapping mode

            if self._main_mode_index == 0:
                # session
                self._control_surface.show_message("Send matrix mode")
                self._setup_mixer(not as_active)
                self._setup_session(as_active, as_enabled)
                self._update_control_channels()
                self._mode_index = self._main_mode_index

            elif self._main_mode_index == 1:
                # Mode 2
                self._control_surface.show_message("Mode 2 [not implemented]")
                self._setup_mixer(not as_active)
                self._setup_session(not as_active, not as_enabled)
                self._update_control_channels()
                self._mode_index = self._main_mode_index

            elif self._main_mode_index == 2:
                # Mode 3
                self._control_surface.show_message("Mode 3 [not implemented]")
                self._setup_mixer(not as_active)
                self._setup_session(not as_active, not as_enabled)
                self._update_control_channels()
                self._mode_index = self._main_mode_index

            elif self._main_mode_index == 3:
                # Mode 4
                self._control_surface.show_message("Mode 4 [not implemented]")
                self._setup_mixer(not as_active)
                self._setup_session(not as_active, not as_enabled)
                self._update_control_channels()
                self._mode_index = self._main_mode_index
            else:
                assert False

            self._session.set_allow_update(True)
            self._zooming.set_allow_update(True)

    def _setup_session(self, as_active, as_navigation_enabled):
        assert isinstance(as_active, type(False))  # assert is boolean
        for button in self._nav_buttons:
            if as_navigation_enabled:
                button.set_on_off_values("Mode.Session.On", "Mode.Session.Off")
            else:
                button.set_on_off_values(
                    "DefaultButton.Disabled", "DefaultButton.Disabled"
                )

        # matrix
        self._activate_matrix(True)
        for scene_index in range(self._session._num_scenes):  # iterate over scenes
            scene = self._session.scene(scene_index)
            if as_active:  # set scene launch buttons
                scene_button = self._side_buttons[scene_index]
                scene_button.set_enabled(as_active)
                scene_button.set_on_off_values(
                    "DefaultButton.Disabled", "DefaultButton.Disabled"
                )
                scene.set_launch_button(scene_button)
            else:
                scene.set_launch_button(None)

            for track_index in range(
                self._session._num_tracks
            ):  # iterate over tracks of a scene -> clip slots
                if as_active:  # set clip slot launch button
                    button = self._matrix.get_button(track_index, scene_index)
                    button.set_on_off_values(
                        "DefaultButton.Disabled", "DefaultButton.Disabled"
                    )
                    button.set_enabled(as_active)
                    scene.clip_slot(track_index).set_launch_button(button)
                else:
                    scene.clip_slot(track_index).set_launch_button(None)

        if as_active:  # zoom
            self._zooming.set_zoom_button(
                self._modes_buttons[0]
            )  # Set Session button as zoom shift button
            self._zooming.set_button_matrix(self._matrix)
            self._zooming.set_scene_bank_buttons(self._side_buttons)
            self._zooming.set_nav_buttons(
                self._nav_buttons[0],
                self._nav_buttons[1],
                self._nav_buttons[2],
                self._nav_buttons[3],
            )
            self._zooming.update()
        else:
            self._zooming.set_zoom_button(None)
            self._zooming.set_button_matrix(None)
            self._zooming.set_scene_bank_buttons(None)
            self._zooming.set_nav_buttons(None, None, None, None)

        if as_navigation_enabled:  # nav buttons (track/scene)
            self._session.set_track_bank_buttons(
                self._nav_buttons[3], self._nav_buttons[2]
            )
            self._session.set_scene_bank_buttons(
                self._nav_buttons[1], self._nav_buttons[0]
            )
        else:
            self._session.set_track_bank_buttons(None, None)
            self._session.set_scene_bank_buttons(None, None)

    # TODO Merge this into above
    def _setup_mixer(self, as_active):
        assert isinstance(as_active, type(False))
        if as_active:
            self._activate_navigation_buttons(True)
            self._activate_scene_buttons(True)
            self._activate_matrix(True)

    def _init_session(self):
        session_height = self._matrix.height()
        if self._session._stop_clip_buttons != None:
            session_height = self._matrix.height() - 1

        for scene_index in range(session_height):
            for track_index in range(self._matrix.width()):
                self._all_buttons.append(
                    self._matrix.get_button(track_index, scene_index)
                )

    def _activate_navigation_buttons(self, active):
        for button in self._nav_buttons:
            button.set_enabled(active)

    def _activate_scene_buttons(self, active):
        for button in self._side_buttons:
            button.set_enabled(active)

    def _activate_matrix(self, active):
        for scene_index in range(8):
            for track_index in range(8):
                self._matrix.get_button(track_index, scene_index).set_enabled(active)

    # Update the channels of the buttons in the user modes..
    def _update_control_channels(self):
        new_channel = self.channel_for_current_mode()
        for button in self._all_buttons:
            button.set_channel(new_channel)
            button.force_next_send()