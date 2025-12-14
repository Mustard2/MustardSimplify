<p align="center">
  <img src="https://github.com/user-attachments/assets/294b511a-9770-42dc-8b2b-beaba2fefc42" width="200" />
</p>


# Mustard Simplify

<img align="right" src="https://github.com/user-attachments/assets/30406ac1-b039-49ca-a7ec-5391e160439e" alt="drawing" width="200"/>

Blender add-on to simplify scenes and boost viewport performance.

This add-on disables certain scene and object features that impact viewport performance with a single click.

It operates non-destructively, meaning no mesh edits are made, and preserves the settings before Simplify is enabled. When Simplify is disabled, object properties (such as modifier visibility and shape key status) are restored to their original state.

## How to install

There are two supported ways to install the add-on:

- (Recommended) Install the add-on as a Blender extension, either from the [website](https://extensions.blender.org/add-ons/mustardsimplify/) or in the Get Extensions panel of Blender settings. **This is the recommended method for installing the add-on, as it ensures automatic updates.**
- Download the [latest version](https://github.com/Mustard2/MustardSimplify/releases/latest) from the Releases page, and install it as a Blender Extension or a Legacy Blender add-on. **Do not download the code from the repository! Only use the .zip files in the Release page.**

## How to use

- Click "Simplify Scene" and the add-on will automatically disable heavy features that could impact viewport performance.
- Use the Settings to select which features should be disabled when Simplify is applied.
- Objects or Collections added to the exceptions list are unaffected by the simplification process (nothing from those objects will be disabled).

For more details, check the [add-on's GitHub wiki](https://github.com/Mustard2/MustardSimplify/wiki).

Note: Enabling "Disable Drivers" will mute all drivers (unless the object is in the Exceptions list). When Simplify is turned off, these drivers will be unmuted. To prevent unintended unmuting, consider adding the affected object to the Exceptions list.

## Credits

- Thanks to all direct contributors to the project (@cl3m3c7, @Ckang3D) and to all people reporting bugs/suggesting features.
- Thanks to @theoldben for their [BlenderNormalGroups](https://github.com/theoldben/BlenderNormalGroups) add-on that I integrated into Mustard Simplify.
- Thanks to Cosmo Mídias for some ideas about the Execution Time feature.
