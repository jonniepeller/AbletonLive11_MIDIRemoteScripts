import logging

from ableton.v2.control_surface import Layer
from ableton.v2.control_surface.elements.button_matrix import ButtonMatrixElement
from ableton.v2.control_surface.mode import AddLayerMode, ModesComponent
from Launchpad_Mini_MK3 import Launchpad_Mini_MK3
from Launchpad_Mini_MK3.skin import skin as default_mk3_skin
from ableton.v2.control_surface.skin import Skin
from ableton.v2.control_surface import merge_skins
from novation.colors import Rgb
from novation.mixer import MixerComponent
from novation.skin import Colors

logger = logging.getLogger(__name__)


class AugmentedColors(Colors):
    class Mixer(Colors.Mixer):
        SendControls = Rgb.PURPLE


# Run it
# cp -r AAAA_Launchpad_Matrix /Volumes/GoogleDrive-107830172388264115015/My\ Drive/Documents/Music\ Production/Ableton\ user\ library/Remote\ Scripts/ && killall Live || echo ''  && sleep 1 && open /Applications/Ableton\ Live\ 11\ Suite.app

augmented_skin = merge_skins(*(default_mk3_skin, Skin(AugmentedColors)))


#  NEED TO RELEASE CONTROL FROM CLIP LAUNCHERS?
class JonnieMixer(MixerComponent):
    def set_send_a_controls(self, controls):
        self._set_send_controls(controls, 1)

    def set_send_b_controls(self, controls):
        self._set_send_controls(controls, 0)


class Launchpad_Mini_MK3_Augmented(Launchpad_Mini_MK3):
    skin = augmented_skin
    mixer_class = JonnieMixer

    # def _create_components(self):
    #     super()._create_components()
    #     self._create_background()
    #     self._create_stop_solo_mute_modes()
    #     self._create_session_modes()
    #     self.__on_layout_switch_value.subject = self._elements.layout_switch

    def _create_stop_solo_mute_modes(self):
        self._stop_solo_mute_modes = ModesComponent(
            name="Stop_Solo_Mute_Modes",
            is_enabled=False,
            support_momentary_mode_cycling=False,
            layer=Layer(cycle_mode_button=self._elements.scene_launch_buttons_raw[7]),
        )
        num_sends = len(self._mixer._song.return_tracks)
        # TODO use this
        bottom_x_rows = self._elements.clip_launch_matrix.submatrix[
            :, (8 - num_sends) : 8
        ]
        row_3 = self._elements.clip_launch_matrix.submatrix[:, 2:3]
        row_4 = self._elements.clip_launch_matrix.submatrix[:, 3:4]
        row_3_4 = self._elements.clip_launch_matrix.submatrix[:, 2:4]
        row_7 = self._elements.clip_launch_matrix.submatrix[:, 6:8]
        row_7_8 = self._elements.clip_launch_matrix.submatrix[:, 6:8]
        row_8 = self._elements.clip_launch_matrix.submatrix[:, 7:8]
        rows = self._elements.clip_launch_matrix

        self._stop_solo_mute_modes.add_mode(
            "launch", None, cycle_mode_button_color="Mode.Launch.On"
        )
        self._stop_solo_mute_modes.add_mode(
            "stop",
            AddLayerMode(self._session, Layer(stop_track_clip_buttons=row_8)),
            cycle_mode_button_color="Session.StopClip",
        )
        self._stop_solo_mute_modes.add_mode(
            "solo",
            AddLayerMode(self._mixer, Layer(solo_buttons=row_8)),
            cycle_mode_button_color="Mixer.SoloOn",
        )
        self._stop_solo_mute_modes.add_mode(
            "mute",
            AddLayerMode(self._mixer, Layer(mute_buttons=row_8)),
            cycle_mode_button_color="Mixer.MuteOff",
        )
        self._stop_solo_mute_modes.add_mode(
            "send_controls",
            AddLayerMode(
                self._mixer,
                Layer(send_a_controls=row_3) + Layer(send_b_controls=row_4),
            ),
            cycle_mode_button_color="Mixer.SendControls",
        )
        self._stop_solo_mute_modes.selected_mode = "send_controls"
        self._stop_solo_mute_modes.set_enabled(True)
