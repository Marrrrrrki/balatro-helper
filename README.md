# Balatro Advisor

A read-only Windows desktop helper for vanilla Balatro on Steam. It reads `save.jkr`, displays the current hand/run state, evaluates possible 1–5 card plays, and estimates replacement-hand value by Monte Carlo sampling.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- No third-party Python packages required (Tkinter is included with standard Windows Python installations)

## Run

1. Extract the ZIP.
2. Open the extracted `BalatroAdvisor` folder.
3. Double-click `run.bat`, or open a terminal there and run:

   ```powershell
   py main.py
   ```

4. If automatic detection does not find your save, click **Open save.jkr** and select it.

The normal Steam save location is:

```text
%APPDATA%\Balatro\<profile number>\save.jkr
```

You can also start with an explicit path:

```powershell
py main.py --save "C:\path\to\save.jkr"
```

## What it does

- Decompresses raw-DEFLATE `.jkr` files.
- Parses the Lua table literal as data. It never executes Lua code.
- Reads current hand, deck, Jokers, blind target, hands/discards, ante and poker-hand levels.
- Evaluates every 1–5 card combination in the current hand.
- Scores base hand chips/mult, card chip values, Bonus/Mult/Glass/Steel enhancements, Foil/Holographic/Polychrome editions, and a documented subset of vanilla Jokers.
- Tests discard candidates by sampling replacement cards from the remaining deck, then finding the best hand in the simulated draw.

## Important scoring limitations

This is an initial advisor, not a perfect clone of Balatro's scoring engine. Joker effects are intentionally partial. Unknown Jokers are listed as unsupported rather than being silently ignored. The current model does not fully simulate all vanilla Jokers, retriggers, seals, probability effects, card destruction, boss-blind restrictions, hand-selection overrides (such as Four Fingers or Shortcut), or every special interaction. The discard EV is a heuristic: it assumes the remaining deck list is the drawable pool and evaluates the best possible follow-up hand after the replacement.

Treat its numbers as estimates, especially when unsupported effects are present. It never writes to `save.jkr`.

## Safety

The application opens save files read-only. It does not edit, overwrite, or re-compress any Balatro file. Balatro can write saves while running; the reader retries briefly if it catches a partial write.
