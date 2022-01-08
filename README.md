# SAWC
#### Static Audio WebM Creator
___
Static Audio WebM Creator is a tool for making primarily music-based WebM files. When run, it offers the user a convenient GUI from which they can select their desired music and album art - it will then generate a WebM fitting their desired output size.

SAWC is tailored to imageboard users primarily - it offers the ability to include audio significantly longer than the  ordinary 5 minute limit on your favorite underwater basket-weaving forums, and offers the highest quality audio for any given upload limit. For those who are truly in a rush, you can also simply drag-and-drop an audio and image file onto the program, and it will automatically create a WebM using the default settings (6MB limit), bypassing the need to use the GUI at all.

SAWC does not currently support batch processing, and currently does not offer an executable (primarily due to size constraints when packaging). If there is sufficient interest, a re-write in C++ or a similarly compiled language may be considered - but currently this is not planned.
With that said, if you have Python installed, you can still use it if you'd like.
SAWC requires the following non-standard modules to be installed:
```
pip install --upgrade PyQt5
pip install --upgrade Pillow
```
Assuming those are installed, you can simply run client.py, either directly or through the aforementioned drag-and-drop approach.
