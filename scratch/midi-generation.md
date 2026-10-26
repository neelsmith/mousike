In Book II of the *Harmonics*, Claudius Ptolemy organizes his tunings around the **tetrachord**—the foundational 4-note unit spanning a Perfect 4th ($4:3$ ratio, or approximately $498.04\text{ cents}$).

Ptolemy insisted on **superparticular ratios** (ratios of the form $\frac{n+1}{n}$) for all microtonal intervals. Because Greek notation is indexed to scale steps (strings) rather than absolute pitch, you can define your pitch values by constructing a **Greater Perfect System** (a 2-octave scale made of two disjunct pairs of conjunct tetrachords plus a bottom tone).

Below is a breakdown of the mathematical ratios, cent values, and step-by-step logic needed to code these pitch values for Method A.

---

### 1. Understanding Tetrachord Division Logic

A tetrachord consists of 4 notes (4th, 3rd, 2nd, and 1st degree) moving downward from the highest pitch to the lowest pitch.
To compute the frequency ratio or cent value of each pitch step within a tetrachord:

* **Ratio:** $\text{Interval Ratio} = \frac{f_{\text{high}}}{f_{\text{low}}}$
* **Cents:** $\text{Cents} = 1200 \times \log_2(\text{Ratio})$

---

### 2. Ptolemy’s Primary Genera & Ratios

Ptolemy defined seven distinct divisions of the tetrachord across the three ancient genera (Diatonic, Chromatic, and Enharmonic). The ratios below represent the **intervals between adjacent notes** inside a single tetrachord, ordered from **lowest interval to highest interval** (bottom to top of the tetrachord).

#### A. Diatonic Genera (Traditional / Scale-like)

1. **Intense (Tense) Diatonic (*Diatonikon Syntonon*)**
* *Ratios:* $16:15$, $9:8$, $10:9$
* *Cents:* $111.73\text{ c}$, $203.91\text{ c}$, $182.40\text{ c}$
* *Note:* This is the classic 5-limit Just Intonation diatonic scale ($16:15 \times 9:8 \times 10:9 = 4:3$).


2. **Soft Diatonic (*Diatonikon Malakon*)**
* *Ratios:* $21:20$, $10:9$, $8:7$
* *Cents:* $84.47\text{ c}$, $182.40\text{ c}$, $231.17\text{ c}$


3. **Tonic Diatonic (*Diatonikon Toniaion*)**
* *Ratios:* $28:27$, $8:7$, $9:8$ (Ptolemy attributes this to Archytas)
* *Cents:* $62.57\text{ c}$, $231.17\text{ c}$, $203.91\text{ c}$


4. **Equable (Even) Diatonic (*Diatonikon Homolon*)**
* *Ratios:* $12:11$, $11:10$, $10:9$
* *Cents:* $150.64\text{ c}$, $165.00\text{ c}$, $182.40\text{ c}$


5. **Ditonica Diatonic (*Diatonikon Ditoniaion*)**
* *Ratios:* $256:243$, $9:8$, $9:8$ (Standard Pythagorean Tuning)
* *Cents:* $90.22\text{ c}$, $203.91\text{ c}$, $203.91\text{ c}$



#### B. Chromatic Genera (Shifting Middle Notes)

1. **Intense Chromatic (*Chroma Syntonon*)**
* *Ratios:* $22:21$, $12:11$, $7:6$
* *Cents:* $80.54\text{ c}$, $150.64\text{ c}$, $266.86\text{ c}$


2. **Soft Chromatic (*Chroma Malakon*)**
* *Ratios:* $28:27$, $15:14$, $6:5$
* *Cents:* $62.57\text{ c}$, $119.44\text{ c}$, $315.64\text{ c}$



#### C. Enharmonic Genus (Featuring Quarter-Tones)

1. **Ptolemy’s Enharmonic (*Enharmonion*)**
* *Ratios:* $46:45$, $24:23$, $5:4$
* *Cents:* $38.05\text{ c}$, $73.68\text{ c}$, $386.31\text{ c}$ (Notice the large major 3rd $5:4$ step paired with microtonal quarter-tone-like steps).



---

### 3. Assembling a Full Scale (The Greater Perfect System)

To build pitch values for an entire piece, stack these tetrachords according to the **Systema Teleion** (Greater Perfect System).

Starting from a base pitch (e.g., $A_2 = 110\text{ Hz}$ or $A_3 = 220\text{ Hz}$):

$$\begin{array}{lll} \mathbf{Note / Degree} & \mathbf{System Connection} & \mathbf{Cumulative Ratio from Proslambanomenos} \\ \hline \text{Proslambanomenos } (A_2) & \text{Bottom note} & 1:1 \text{ (Base Fundamental)} \\ \text{Hypate Hypaton } (B_2) & \text{Disjunction step} & 9:8 \text{ (Whole Tone, } 203.91\text{ c)} \\ \text{Parhypate Hypaton } (C_3) & \text{Lowest tetrachord step} & 9/8 \times \text{Interval}_1 \\ \text{Lichanos Hypaton } (D_3) & \text{Middle tetrachord step} & 9/8 \times \text{Interval}_1 \times \text{Interval}_2 \\ \text{Hypate Meson } (E_3) & \text{Top of 1st Tetrachord} & 4:3 \text{ (Fixed Pure 4th, } 498.04\text{ c)} \\ \text{Parhypate Meson } (F_3) & \text{Lowest step (2nd Tetrachord)} & 4/3 \times \text{Interval}_1 \\ \text{Lichanos Meson } (G_3) & \text{Middle step (2nd Tetrachord)} & 4/3 \times \text{Interval}_1 \times \text{Interval}_2 \\ \text{Mese } (A_3) & \text{Top of 2nd Tetrachord} & 3:2 \text{ (Fixed Pure 5th, } 701.96\text{ c)} \\ \text{Paramese } (B_3) & \text{Disjunction step} & 3/2 \times 9/8 = 27:16 \text{ (or } 9:4\text{ octave relation)} \\ \dots & \text{Upper Tetrachords} & \dots \end{array}$$

*Note: The **"Fixed" notes** (*Proslambanomenos, Hypate Hypaton, Hypate Meson, Mese, Paramese, Nete*) remain constant across all tuning systems. Only the **"Movable" notes** (*Parhypate* and *Lichanos*) shift when switching between Ptolemy's different genera.*

---

### 4. Implementation Formula for Method A (MIDI Pitch Bending)

For each target pitch in your tuning system:

1. **Calculate Target Frequency ($f_{\text{target}}$):**

$$f_{\text{target}} = f_{\text{base}} \times \text{Cumulative Ratio}$$


2. **Determine Nearest 12-TET MIDI Note ($N$):**

$$N = \text{round}\left(69 + 12 \times \log_2\left(\frac{f_{\text{target}}}{440}\right)\right)$$


3. **Calculate Frequency of that 12-TET Note ($f_{\text{MIDI}}$):**

$$f_{\text{MIDI}} = 440 \times 2^{\frac{N - 69}{12}}$$


4. **Calculate Pitch Bend Offset in Cents ($\Delta c$):**

$$\Delta c = 1200 \times \log_2\left(\frac{f_{\text{target}}}{f_{\text{MIDI}}}\right)$$


5. **Convert Cent Offset to MIDI Pitch Bend Value (14-bit integer, assuming $\pm 2$ semitone bend range):**

$$\text{MIDI Bend Value} = 8192 + \text{round}\left(\Delta c \times \frac{8192}{200}\right)$$



*(Where `8192` is center/no bend, `0` is $-200\text{ cents}$, and `16383` is $+200\text{ cents}$)*.
