# Mustard Simplify

A scene simplifier for Blender to increase viewport performance

## How to install

Install the .py file (**not** the archive file) as a standard Blender add-on.

*Or load the .py file in the Blender Text Editor and run it as a script, but the add-on will only be valid in the current scene and in the current Blender session.*

## How to use

Click on Simplify Scene and the add-on takes care of disabling all heavy stuffs that might affect your viewport performance.

The add-on acts on the Objects in the scene non-destructively (no mesh is edited in any way) and remembering the settings before enabling Simplify. That is, disabling Simplify, the Object (modifier viewport visibility status shape key mute status, etc..) will be reverted to pre-Simplify status.

The add-on will **not** hide any Object from the scene. If you have very heavy mesh, consider to disable them while animating.

## Benchmarks

From some preliminarly benchmarks, I got even +100% on some randomly selected scenes from other people (I could not use my scenes as they are already optimized with MustardUI Simplify).
