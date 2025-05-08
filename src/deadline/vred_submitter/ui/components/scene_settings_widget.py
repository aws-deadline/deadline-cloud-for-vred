# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Defines the UI design for top-level scene-specific render settings ("Job-specific settings")
Acts as the main control point for branching out these responsibilities to other classes:
    - handling of Qt callbacks for UI elements
    - populating VRED runtime-level values into UI elements
"""

import itertools
from typing import Type

from .constants import Constants
from ...qt_components import AutoSizedComboBox, AutoSizedButton, CustomGroupBox
from .scene_settings_callbacks import SceneSettingsCallbacks
from .scene_settings_logic import SceneSettingsLogic

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import (QDoubleValidator, QIntValidator)
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
    QVBoxLayout
)


class SceneSettingsWidget(QWidget):
    """Represents a widget containing top-level scene-specific render settings ("Job-specific settings")"""

    DEFAULT_WIDGET_ALIGNMENT = Qt.AlignLeft | Qt.AlignTop

    def __init__(self, initial_settings: "RenderSubmitterUISettings", parent: "QWidget" = None):
        """
        Builds the UI, connects UI elements to their respective callbacks, initializes a UI logic handler.
        param: initial_settings: maintains values for all render submission parameters.
        param: parent: parent widget for this UI component.
        """
        super().__init__(parent=parent)
        self.init_complete = False
        self.parent = parent
        self.callbacks = SceneSettingsCallbacks(self)
        self.parent.installEventFilter(self)
        self._build_ui()
        self.logic = SceneSettingsLogic(self, initial_settings)
        self.init_complete = True

    def eventFilter(self, obj, event):
        """
        Override to intercept events for the parent dialog; handles the close event by de-registering
        past registered callbacks. Other events are passed through to the default handler.
        param: obj: the object that triggered the event
        param: event: event: that was triggered
        return: False for close events; super().eventFilter for all other events
        """
        if obj == self.parent and event.type() == QEvent.Close:
            self.callbacks.deregister_all_callbacks()
            # Let the event continue to be processed
            return False
        return super().eventFilter(obj, event)

    def _build_ui(self) -> None:
        """
        High-level routine for building the render settings user interface that comprises "Job-specific settings"
        content. (It will be embedded under the "Job-specific settings" tab of the standard Deadline Cloud dialog.)

        Note: UI elements (defined later) need to be synchronized with those exposed in template.yaml file. This
        is necessary because callback functions, runtime value injection, and VRED-specific personalization needs to
        access (and be applied to) UI elements. Remember to also synchronize constraints on values.
        param: settings: the render settings from which to initialize UI controls
        """
        # The main layout contains group box-based sections
        layout_main = self._create_main_layout_with_sections()
        # A grid layout pairs with each of those sections and parents to matching layouts
        grid_layout_general = QGridLayout()
        grid_layout_render = QGridLayout()
        grid_layout_sequencer = QGridLayout()
        grid_layout_tiling = QGridLayout()
        layout_main.addLayout(grid_layout_general)
        self.group_box_render_options.layout().addLayout(grid_layout_render)
        self.group_box_sequencer_options.layout().addLayout(grid_layout_sequencer)
        self.group_box_tiling_settings.layout().addLayout(grid_layout_tiling)
        # Create lower-level UI controls for each group. Keep the UI elements positioned relatively with a row counter.
        row_counter = itertools.count()
        self._build_general_options(grid_layout_general, row_counter)
        self._build_render_options(grid_layout_render, row_counter)
        self._build_sequencer_options(grid_layout_sequencer, row_counter)
        self._build_tiling_settings(grid_layout_tiling, row_counter)

    def _create_main_layout_with_sections(self) -> QVBoxLayout:
        """
        Create the main layout, adding group boxes for main sections.
        return: the main layout
        """
        layout_main = QVBoxLayout(self)
        self.group_box_render_options = CustomGroupBox(Constants.SECTION_RENDER_OPTIONS)
        self.group_box_sequencer_options = CustomGroupBox(Constants.SECTION_SEQUENCER_OPTIONS)
        self.group_box_tiling_settings = CustomGroupBox(Constants.SECTION_TILING_SETTINGS)
        for group_box in [self.group_box_render_options, self.group_box_sequencer_options,
                          self.group_box_tiling_settings]:
            group_box.setLayout(QVBoxLayout())
            layout_main.addWidget(group_box, self.DEFAULT_WIDGET_ALIGNMENT)
        return layout_main

    def _build_general_options(self, grid_layout: QGridLayout, row_counter: int) -> None:
        """
        Build general options section with UI elements defined below.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        """
        self.render_job_type_label = QLabel(Constants.JOB_TYPE_LABEL)
        self.render_job_type_label.setToolTip(Constants.JOB_TYPE_LABEL_DESCRIPTION)
        self.render_job_type_widget = AutoSizedComboBox()
        self.render_job_type_widget.currentIndexChanged.connect(self.callbacks.job_type_changed_callback)
        job_type_layout = QHBoxLayout()
        job_type_layout.addWidget(self.render_job_type_label)
        job_type_layout.addWidget(self.render_job_type_widget)
        grid_layout.addLayout(job_type_layout, next(row_counter), 0, self.DEFAULT_WIDGET_ALIGNMENT)

    def _build_render_options(self, grid_layout: QGridLayout, row_counter: int) -> None:
        """
        Build Render Options section with UI elements defined below.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        """
        iter_value = lambda x: int(x.__reduce__()[1][0])
        self._add_render_output_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self.render_view_widget = self._add_label_and_widget(
            grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value, Constants.RENDER_VIEW_LABEL,
            Constants.RENDER_VIEW_LABEL_DESCRIPTION, AutoSizedComboBox
        )
        self._add_image_size_preset_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_image_size_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_printing_size_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_resolution_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_render_animation_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self.render_quality_widget = self._add_label_and_widget(
            grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value, Constants.RENDER_QUALITY_LABEL,
            Constants.RENDER_QUALITY_LABEL_DESCRIPTION, AutoSizedComboBox
        )
        self.dlss_quality_widget = self._add_label_and_widget(
            grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value, Constants.DLSS_QUALITY_LABEL,
            Constants.DLSS_QUALITY_LABEL_DESCRIPTION,
            AutoSizedComboBox
        )
        self.ss_quality_widget = self._add_label_and_widget(
            grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value, Constants.SS_QUALITY_LABEL,
            Constants.SS_QUALITY_LABEL_DESCRIPTION, AutoSizedComboBox
        )
        self._add_animation_type_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_animation_clip_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self.use_clip_range_widget = QCheckBox(Constants.USE_CLIP_RANGE_LABEL)
        self.use_clip_range_widget.setToolTip(Constants.USE_CLIP_RANGE_LABEL_DESCRIPTION)
        self.use_clip_range_widget.stateChanged.connect(self.callbacks.use_clip_range_changed_callback)
        grid_layout.addWidget(self.use_clip_range_widget, next(row_counter), 0, self.DEFAULT_WIDGET_ALIGNMENT)
        self._add_frame_range_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_frames_per_task_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)

    def _build_sequencer_options(self, grid_layout: QGridLayout, row_counter: int) -> None:
        """
        Build sequencer options section with UI elements defined below.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        """
        iter_value = lambda x: int(x.__reduce__()[1][0])
        self.sequence_name_label = QLabel(Constants.SEQUENCE_NAME_LABEL)
        self.sequence_name_label.setToolTip(Constants.SEQUENCE_NAME_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.sequence_name_label, iter_value(row_counter), 0, self.DEFAULT_WIDGET_ALIGNMENT)
        self.sequence_name_widget = QLineEdit("")
        self.sequence_name_widget.setFixedWidth(Constants.LONG_TEXT_ENTRY_WIDTH)
        grid_layout.addWidget(self.sequence_name_widget, iter_value(row_counter), 1, self.DEFAULT_WIDGET_ALIGNMENT)

    def _build_tiling_settings(self, grid_layout: QGridLayout, row_counter: int) -> None:
        """
        Build tiling settings section with UI elements defined below.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        """
        iter_value = lambda x: int(x.__reduce__()[1][0])
        self._add_region_rendering_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT)
        self._add_tiles_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_assembly_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_abort_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_assemble_over_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)
        self._add_background_image_controls(grid_layout, row_counter, self.DEFAULT_WIDGET_ALIGNMENT, iter_value)

    def _add_label_and_widget(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                              iter_value: int, label_text: str, tooltip: str, widget_cls: Type[QWidget]) -> QWidget:
        """
        Helper method to add a label and widget pair to a grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        param: label_text: text for the label
        param: widget_cls: the type of QWidget-based widget to create and add to the grid layout
        return: the created widget instance based on widget_cls
        """
        label = QLabel(label_text)
        label.setToolTip(tooltip)
        new_widget = widget_cls()
        grid_layout.addWidget(label, iter_value(row_counter), 0, alignment)
        grid_layout.addWidget(new_widget, next(row_counter), 1, alignment)
        return new_widget

    def _add_render_output_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                    iter_value: int) -> None:
        """
        Add render output UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.render_output_label = QLabel(Constants.RENDER_OUTPUT_LABEL)
        self.render_output_label.setToolTip(Constants.RENDER_OUTPUT_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.render_output_label, iter_value(row_counter), 0, alignment)
        self.render_output_widget = QLineEdit("")
        self.render_output_widget.setFixedWidth(Constants.VERY_LONG_TEXT_ENTRY_WIDTH)
        self.render_output_button = AutoSizedButton(Constants.ELLIPSIS_LABEL)
        self.render_output_button.pressed.connect(self.callbacks.get_render_output_callback)
        render_output_layout = QHBoxLayout()
        render_output_layout.addWidget(self.render_output_widget)
        render_output_layout.addWidget(self.render_output_button)
        grid_layout.addLayout(render_output_layout, next(row_counter), 1, alignment)

    def _add_image_size_preset_controls(self, grid_layout, row_counter, alignment, iter_value):
        """
        Add image size preset UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.image_size_presets_label = QLabel(Constants.IMAGE_SIZE_PRESETS_LABEL)
        self.image_size_presets_label.setToolTip(Constants.IMAGE_SIZE_PRESETS_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.image_size_presets_label, iter_value(row_counter), 0, alignment)
        self.image_size_presets_widget = AutoSizedComboBox()
        self.image_size_presets_widget.currentIndexChanged.connect(
            self.callbacks.image_size_preset_selection_changed_callback)
        grid_layout.addWidget(self.image_size_presets_widget, next(row_counter), 1, alignment)

    def _add_image_size_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                 iter_value: int) -> None:
        """
        Add image size UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.image_size_label = QLabel(Constants.IMAGE_SIZE_LABEL)
        self.image_size_label.setToolTip(Constants.IMAGE_SIZE_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.image_size_label, iter_value(row_counter), 0, alignment)
        self.image_size_x_widget = QLineEdit("")
        self.image_size_x_widget.setFixedWidth(Constants.SHORT_TEXT_ENTRY_WIDTH)
        self.image_size_x_widget.returnPressed.connect(self.callbacks.image_size_text_changed_callback)
        self.image_size_y_widget = QLineEdit("")
        self.image_size_y_widget.setFixedWidth(Constants.SHORT_TEXT_ENTRY_WIDTH)
        self.image_size_y_widget.returnPressed.connect(self.callbacks.image_size_text_changed_callback)
        image_size_layout = QHBoxLayout()
        image_size_layout.addWidget(self.image_size_x_widget)
        image_size_layout.addWidget(self.image_size_y_widget)
        grid_layout.addLayout(image_size_layout, next(row_counter), 1, alignment)
        image_size_validator = QIntValidator(Constants.MIN_IMAGE_DIMENSION, Constants.MAX_IMAGE_DIMENSION)
        self.image_size_x_widget.setValidator(image_size_validator)
        self.image_size_y_widget.setValidator(image_size_validator)

    def _add_printing_size_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                    iter_value: int) -> None:
        """
        Add printing size UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.printing_size_label = QLabel(Constants.PRINTING_SIZE_LABEL)
        self.printing_size_label.setToolTip(Constants.PRINTING_SIZE_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.printing_size_label, iter_value(row_counter), 0, alignment)
        self.printing_size_x_widget = QLineEdit("")
        self.printing_size_x_widget.setFixedWidth(Constants.SHORT_TEXT_ENTRY_WIDTH)
        self.printing_size_x_widget.returnPressed.connect(self.callbacks.printing_size_text_changed_callback)
        self.printing_size_y_widget = QLineEdit("")
        self.printing_size_y_widget.setFixedWidth(Constants.SHORT_TEXT_ENTRY_WIDTH)
        self.printing_size_y_widget.returnPressed.connect(self.callbacks.printing_size_text_changed_callback)
        printing_size_layout = QHBoxLayout()
        printing_size_layout.addWidget(self.printing_size_x_widget)
        printing_size_layout.addWidget(self.printing_size_y_widget)
        grid_layout.addLayout(printing_size_layout, next(row_counter), 1, alignment)
        printing_size_validator = QDoubleValidator(Constants.MIN_IMAGE_DIMENSION, Constants.MAX_IMAGE_DIMENSION,
                                                   Constants.PRINTING_PRECISION_DIGITS_COUNT)
        self.printing_size_x_widget.setValidator(printing_size_validator)
        self.printing_size_y_widget.setValidator(printing_size_validator)

    def _add_resolution_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                 iter_value: int) -> None:
        """
        Add resolution UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.resolution_label = QLabel(Constants.RESOLUTION_LABEL)
        self.resolution_label.setToolTip(Constants.RESOLUTION_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.resolution_label, iter_value(row_counter), 0, alignment)
        self.resolution_widget = QLineEdit("")
        self.resolution_widget.setFixedWidth(Constants.SHORT_TEXT_ENTRY_WIDTH)
        self.resolution_widget.returnPressed.connect(self.callbacks.resolution_text_changed_callback)
        grid_layout.addWidget(self.resolution_widget, next(row_counter), 1, alignment)
        self.resolution_widget.setValidator(QIntValidator(Constants.MIN_DPI, Constants.MAX_DPI))

    def _add_render_animation_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                       iter_value: int) -> None:
        """
        Add render animation and GPU ray tracing UI elements to the grid layout."""
        self.render_animation_widget = QCheckBox(Constants.RENDER_ANIMATION_LABEL)
        self.render_animation_widget.setToolTip(Constants.RENDER_ANIMATION_LABEL_DESCRIPTION)
        self.render_animation_widget.stateChanged.connect(self.callbacks.job_type_changed_callback)
        grid_layout.addWidget(self.render_animation_widget, iter_value(row_counter), 0, alignment)
        self.gpu_ray_tracing_widget = QCheckBox(Constants.USE_GPU_RAY_TRACING_LABEL)
        self.gpu_ray_tracing_widget.setToolTip(Constants.USE_GPU_RAY_TRACING_LABEL_DESCRIPTION)
        self.gpu_ray_tracing_widget.stateChanged.connect(self.callbacks.job_type_changed_callback)
        grid_layout.addWidget(self.gpu_ray_tracing_widget, next(row_counter), 1, alignment)

    def _add_animation_type_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                     iter_value: int) -> None:
        """
        Add animation type UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.animation_type_label = QLabel(Constants.ANIMATION_TYPE_LABEL)
        self.animation_type_label.setToolTip(Constants.ANIMATION_TYPE_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.animation_type_label, iter_value(row_counter), 0, alignment)
        self.animation_type_widget = AutoSizedComboBox()
        self.animation_type_widget.currentIndexChanged.connect(
            self.callbacks.animation_type_selection_changed_callback)
        grid_layout.addWidget(self.animation_type_widget, next(row_counter), 1, alignment)

    def _add_animation_clip_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                     iter_value: int) -> None:
        """
        Add animation clip UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.animation_clip_label = QLabel(Constants.ANIMATION_CLIP_LABEL)
        self.animation_clip_label.setToolTip(Constants.ANIMATION_CLIP_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.animation_clip_label, iter_value(row_counter), 0, alignment)
        self.animation_clip_widget = AutoSizedComboBox()
        self.animation_clip_widget.setFixedWidth(Constants.MODERATE_TEXT_ENTRY_WIDTH)
        self.animation_clip_widget.currentIndexChanged.connect(
            self.callbacks.animation_clip_selection_changed_callback)
        grid_layout.addWidget(self.animation_clip_widget, next(row_counter), 1, alignment)

    def _add_frame_range_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                  iter_value: int) -> None:
        """
        Add frame range UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.frame_range_label = QLabel(Constants.FRAME_RANGE_LABEL)
        self.frame_range_label.setToolTip(Constants.FRAME_RANGE_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.frame_range_label, iter_value(row_counter), 0, alignment)
        self.frame_range_widget = QLineEdit("")
        self.frame_range_widget.setFixedWidth(Constants.LONG_TEXT_ENTRY_WIDTH)
        grid_layout.addWidget(self.frame_range_widget, next(row_counter), 1, alignment)

    def _add_frames_per_task_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                      iter_value: int) -> None:
        """
        Add frames per task UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.frames_per_task_label = QLabel(Constants.FRAMES_PER_TASK_LABEL)
        self.frames_per_task_label.setToolTip(Constants.FRAMES_PER_TASK_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.frames_per_task_label, iter_value(row_counter), 0, alignment)
        self.frames_per_task_widget = QSpinBox()
        self.frames_per_task_widget.setFixedWidth(Constants.SHORT_TEXT_ENTRY_WIDTH)
        grid_layout.addWidget(self.frames_per_task_widget, next(row_counter), 1, alignment)
        self.frames_per_task_widget.setMinimum(Constants.MIN_FRAMES_PER_TASK)

    def _add_region_rendering_controls(self, grid_layout: QGridLayout, row_counter: int,
                                       alignment: Qt.Alignment) -> None:
        """
        Add region rendering UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        """
        self.enable_region_rendering_widget = QCheckBox(Constants.ENABLE_REGION_RENDERING_LABEL)
        self.enable_region_rendering_widget.setToolTip(Constants.ENABLE_REGION_RENDERING_LABEL_DESCRIPTION)
        self.enable_region_rendering_widget.stateChanged.connect(
            self.callbacks.enable_region_rendering_changed_callback)
        grid_layout.addWidget(self.enable_region_rendering_widget, next(row_counter), 0, 1, 1, alignment)

    def _add_tiles_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                            iter_value: int) -> None:
        """
        Add tiles in X and Y UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.tiles_in_x_label = QLabel(Constants.TILES_IN_X_LABEL)
        self.tiles_in_x_label.setToolTip(Constants.TILES_IN_X_LABEL_DESCRIPTION)
        self.tiles_in_x_widget = QSpinBox()
        self.tiles_in_x_widget.setFixedWidth(Constants.VERY_SHORT_TEXT_ENTRY_WIDTH)
        tiles_in_x_layout = QHBoxLayout()
        tiles_in_x_layout.addWidget(self.tiles_in_x_label)
        tiles_in_x_layout.addWidget(self.tiles_in_x_widget)
        grid_layout.addLayout(tiles_in_x_layout, iter_value(row_counter), 0, alignment)
        self.tiles_in_y_label = QLabel(Constants.TILES_IN_Y_LABEL)
        self.tiles_in_y_label.setToolTip(Constants.TILES_IN_Y_LABEL_DESCRIPTION)
        self.tiles_in_y_widget = QSpinBox()
        self.tiles_in_y_widget.setFixedWidth(Constants.VERY_SHORT_TEXT_ENTRY_WIDTH)
        tiles_in_y_layout = QHBoxLayout()
        tiles_in_y_layout.addWidget(self.tiles_in_y_label)
        tiles_in_y_layout.addWidget(self.tiles_in_y_widget)
        grid_layout.addLayout(tiles_in_y_layout, next(row_counter), 1, alignment)
        self.tiles_in_x_widget.setMinimum(Constants.MIN_TILES_PER_DIMENSION)
        self.tiles_in_x_widget.setMaximum(Constants.MAX_TILES_PER_DIMENSION)
        self.tiles_in_y_widget.setMinimum(Constants.MIN_TILES_PER_DIMENSION)
        self.tiles_in_y_widget.setMaximum(Constants.MAX_TILES_PER_DIMENSION)

    def _add_assembly_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                               iter_value: int) -> None:
        """
        Add assembly job UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.submit_dependent_assembly_widget = QCheckBox(Constants.SUBMIT_DEPENDENT_ASSEMBLY_JOB_LABEL)
        self.submit_dependent_assembly_widget.setToolTip(Constants.SUBMIT_DEPENDENT_ASSEMBLY_JOB_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.submit_dependent_assembly_widget, iter_value(row_counter), 0, alignment)
        self.cleanup_tiles_widget = QCheckBox(Constants.CLEAN_UP_TILES_AFTER_ASSEMBLY_LABEL)
        self.cleanup_tiles_widget.setToolTip(Constants.SUBMIT_DEPENDENT_ASSEMBLY_JOB_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.cleanup_tiles_widget, next(row_counter), 1, alignment)

    def _add_abort_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                            iter_value: int) -> None:
        """
        Add abort handling UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.abort_on_missing_tiles_widget = QCheckBox(Constants.ABORT_ON_MISSING_TILES_LABEL)
        self.abort_on_missing_tiles_widget.setToolTip(Constants.ABORT_ON_MISSING_TILES_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.abort_on_missing_tiles_widget, iter_value(row_counter), 0, alignment)
        self.abort_on_missing_background_widget = QCheckBox(Constants.ABORT_ON_MISSING_BACKGROUND_LABEL)
        self.abort_on_missing_background_widget.setToolTip(Constants.ABORT_ON_MISSING_BACKGROUND_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.abort_on_missing_background_widget, next(row_counter), 1, alignment)

    def _add_assemble_over_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                    iter_value: int) -> None:
        """
        Add assemble over UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.assemble_over_label = QLabel(Constants.ASSEMBLE_OVER_LABEL)
        self.assemble_over_label.setToolTip(Constants.ASSEMBLE_OVER_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.assemble_over_label, iter_value(row_counter), 0, alignment)
        self.assemble_over_widget = AutoSizedComboBox()
        self.assemble_over_widget.currentIndexChanged.connect(self.callbacks.assemble_over_changed_callback)
        grid_layout.addWidget(self.assemble_over_widget, next(row_counter), 1, alignment)

    def _add_background_image_controls(self, grid_layout: QGridLayout, row_counter: int, alignment: Qt.Alignment,
                                       iter_value: int) -> None:
        """
        Add background image UI elements to the grid layout.
        param: grid_layout: the grid layout to which UI elements are added
        param: row_counter: tracks row number that UI elements added
        param: alignment: alignment for the label and widget
        param: iter_value: function to get the next row counter value
        """
        self.backgroundImageLabel = QLabel(Constants.BACKGROUND_IMAGE_LABEL)
        self.backgroundImageLabel.setToolTip(Constants.BACKGROUND_IMAGE_LABEL_DESCRIPTION)
        grid_layout.addWidget(self.backgroundImageLabel, iter_value(row_counter), 0, alignment)
        self.background_image_widget = QLineEdit("")
        self.background_image_widget.setFixedWidth(Constants.LONG_TEXT_ENTRY_WIDTH)
        self.background_image_button = AutoSizedButton(Constants.ELLIPSIS_LABEL)
        self.background_image_button.pressed.connect(self.callbacks.get_background_file_callback)
        background_image_layout = QHBoxLayout()
        background_image_layout.addWidget(self.background_image_widget)
        background_image_layout.addWidget(self.background_image_button)
        grid_layout.addLayout(background_image_layout, iter_value(row_counter), 1, alignment)

    def update_settings(self, settings: "RenderSubmitterUISettings") -> None:
        """
        Update a scene settings object with the latest UI values using the OpenJD typing convention.
        Note: this callback is invoked by the Deadline Cloud API; callback is unreferenced in submitter code.
        param: setting : maintains values for all render submission parameters
        """
        self.logic.update_settings_callback(settings)
