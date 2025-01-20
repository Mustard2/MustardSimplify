<p align="center">
  <img src="https://github.com/user-attachments/assets/59d43718-e0f7-4cf3-88e4-d079df0d92fd" width="200" />
</p>

# Mustard Simplify

<img align="right" src="https://github.com/user-attachments/assets/30406ac1-b039-49ca-a7ec-5391e160439e" alt="drawing" width="200"/>

A scene simplifier for Blender to increase viewport performance.

The add-on essentially disables some scene/object features that affect Viewport performance with one click.

It acts on the Objects in the scene non-destructively (no mesh is edited in any way) and remembering the settings before enabling Simplify. That is, disabling Simplify, the Object (modifier viewport visibility status shape key mute status, etc..) will be reverted to pre-Simplify status.

## How to install

Download the [latest version](https://github.com/Mustard2/MustardSimplify/releases/tag/2025.1.0) from the Releases page, and install it as a Blender Extension or a Legacy Blender add-on.

**Do not download the code from the repository! Only use the .zip files in the Release page.**

## How to use

- Click on Simplify Scene and the add-on takes care of disabling all heavy stuffs that might affect your viewport performance.
- Objects added as exceptions are not part of the Simplify process (nothing from that Object is disabled)
- Use the Modifiers options to choose which Modifiers to disable with Simplify

Note that Drivers will disable all drivers (if the Object is not in the exceptions). When Simplify is disabled, all those drivers are unmuted. Thus if you want to prevent unwanted unmuting of drivers, consider to add the affected Object to the exceptions.

## Benchmarks

From some preliminarly benchmarks, I got even +100% on some randomly selected scenes from other people (I could not use my scenes as they are already optimized with MustardUI Simplify).
