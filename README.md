# X-AVR

**X-AVR** is an XCode template for generating `AVR C` projects.
The plan is to also add support for `AVR C++` and `Arduino` projects,
with full support for all the Arduino classes.

At that point, I'll probably rename the project and break all your
inbound links. :)

## Requirements

* OS X and Xcode
* The Arduino IDE installed in /Applications

## How It Works

**X-AVR** is a Python script which uses the prebuilt Arduino AVR GCC tools and
`avrdude` to generate and install an XCode `TemplateInfo.plist` file.
This template can be used to create `AVR C` XCode projects with a `Makefile`
to build and upload the program to an `AVR` chip.

This is nice because it means we can reuse the work that Arduino does in
building stable compiler releases.

### Differences To Arduino

*Note*: This template does not generate projects using *the Arduino extensions*.
The generated project uses the `C` language and the `avr-libc` library.

For example, activating pin 13 on an Arduino, using `avr-libc` looks like this:

```C
DDRB |= _BV(PB5)
PORTB |= _BV(PB5)
```

and not:

```C
pinMode(13, OUTPUT)
digitalWrite(13, HIGH)
```

# Motivation

The Arduino IDE is limited. It's good enough for beginners, but there's a
lot of magic that happens behind the scenes that advanced programmers
might not like.

Also, there's no autocomplete.

To fix this, the `X-AVR` project template sets up a *fake* build target
(called `index`) which uses clang to enable XCode to parse and index
your project code.

`X-AVR` also configures the following variables for your build:
* `HEADER_SEARCH_PATHS`: So that XCode can index the `avr-libc` headers and include their definitions (port and register names, functions, etc.) in the autocomplete suggestions
* `GCC_PREPROCESSOR_DEFINITIONS`: The selected MCU macro is set (e.g. `__AVR_ATmega328__`) to get accurate autocomplete over the port and register names. `F_CPU` macro is also set (otherwise the indexing would encouter errors)

Also, `X-AVR`, and unlike many other `Makefile`s and templates, automatically picks up all the `.c` and `.h` files in your project.

# Usage

Clone this repository or download the source zip somewhere in your mac and run `python setup.py` to generate and install the XCode project template.

The previous step need only be run once (or whenever you install a new `avr-gcc` version).

Once the template is installed, you should see an `xavr` entry in the new project wizard in XCode.

The wizard page lets you select the target MCU, its frequency and the programmer to be used to upload the program.

After the wizard is done, hit `Cmd+B` to build the project.
** The first build will fail. But that's *normal* ** (a first run is needed to generate the dependencies maps).
Just rebuild a second time and it should pass.

The project is created with the following targets:

* `All`: performs a clean build and uploads the generated hex to the target MCU
* `Build`: performs a clean build
* `Upload`: uploads the generated hex to the target MCU
* `Clean`: deletes the build artifcats
* `Index`: a *trick* target to get XCode autocompletion to work. You're not supposed to interact with this target

Also check [Using XCode for AVR C developement](http://jawher.me/2014/03/21/using-xcode-avr-c/) for more detailed instructions and screenshots.

# Credits

## Icon

The template icon was created using GIMP and includes a [microchip icon](http://thenounproject.com/term/microchip/31537/)
designed by Lutz Schubert from the Noun Project and published under the Creative Commons – Attribution (CC BY 3.0) license.

## Makefile

The template's `Makefile` is based on the one written by Eric B. Weddington, Jörg Wunsch, et al.

## Template

This template was inspired by the [embedXcode](http://embedxcode.weebly.com/) XCode template.

# License

See `LICENSE` for details (hint: it's MIT).
