# X++ v0.4.5 Release Notes – Package Management & Full Standard Libraries

X++ v0.4.5 introduces a decentralized package manager and a full suite of standard libraries spanning mathematics, web development, GUI/graphics, gaming, animations, and system utilities.

Every single standard library is verified and supported across all 5 RNMs:
`XCOM`, `XITR`, `ZCOM`, `ZITR`, `ZJIT`.

---

## 1. Decentralized Package Management (XPM)

Install any X++ library hosted on GitHub or local paths:

```bash
# Install a library from any GitHub repository
x install github.com/<owner>/<repo>
x install <owner>/<repo>

# Install all dependencies declared in xpp.json
x install

# Uninstall a package
x remove <package>

# List installed packages (local & global)
x list

# Update package(s)
x update [package]

# Initialize a new X++ package/project
x init [project_name]
```

### In-Code Package Imports
```xpp
use "github.com/owner/repo"
# or
use mylib
```

Packages are installed into `./xpp_packages/<lib>/` (or globally in `~/.xpp/packages/` via `--global`). A deterministic `xpp.json` and `xpp.lock` manage versions and exact commit pins.

---

## 2. Standard Libraries (All 5 RNMs Supported)

All libraries work seamlessly with `XCOM`, `XITR`, `ZCOM`, `ZITR`, and `ZJIT`:

### Mathematical Libraries
- **`mathX`**: Trigonometry, hyperbolic, combinatorics, logarithms, powers, statistics, constants (`pi`, `e`, `tau`, `phi`, `inf`, `nan`), gcd, lcm, factorial, prime testing.
- **`Xsci`**: Scipy counterpart for XPP. Numerical minimization/optimization, root finding, curve fitting, Simpson/trapezoid quadrature, 1D interpolation, FFT/IFFT, lowpass filtering, Bessel functions, and probability distributions (`norm_pdf`, `norm_cdf`, `norm_ppf`, `poisson_pmf`).
- **`Xnum`**: Numpy counterpart for XPP. Multidimensional `NDArray`, `zeros`, `ones`, `full`, `eye`, `arange`, `linspace`, matrix reshaping, transposition, matrix multiplication `dot`/`matmul`, axis aggregations (`sum`, `mean`, `std`, `min`, `max`, `clip`).
- **`Xlin`**: Linear algebra module. Determinants (`det`), matrix inversion (`inv`), system solver (`solve`), trace, QR decomposition, LU decomposition with partial pivoting, and eigenvalue/eigenvector computation (`eig`).
- **`XCAS`**: Computer Algebra System. Symbolic expression trees (`expr`), differentiation (`diff`), integration (`integrate`), algebraic simplification (`simplify`), substitution (`subst`), and equation solving (`solve`).
- **`XCalculus`**: Limits, derivatives (order 1..n), partial derivatives, Jacobian matrices, Hessian matrices, single/double/triple definite integrals, gradient, divergence, curl, and Laplacian.
- **`Xplotlib`**: Matplotlib counterpart for XPP. 2D plots (`plot`, `scatter`, `bar`, `hist`), 3D plots (`plot3d`, `scatter3d`, `surface3d`), 4D animated plots (`animate`), SVG output, and high-resolution ASCII terminal visualization.

### Web Related Libraries
- **`ScrapeX`**: Web scraping module. HTTP fetch/get/post, HTML DOM parser, CSS selector queries (`select`, `select_one`), table extractors, link extractors, and image extractors.
- **`XWeb`**: Full-stack web page & static site generator. Semantic HTML builder (`div`, `p`, `h1..h6`, `button`, etc.), responsive CSS compiler (`stylesheet`, `style`), JS injection, router, and static site exporter (`export_static`).
- **`XWview`**: Desktop webview and embedded web display library. Create native windows, load URLs/HTML, evaluate JS, and bidirectional communication.

### Development Libraries
- **`GraphiX`**: 2D vector & canvas graphics engine. Primitives (`rect`, `circle`, `line`, `polygon`, `text`, `path`), matrix transforms, styling via standard CSS (`apply_css`), and SVG export.
- **`XGUI`**: Desktop GUI library. Component architecture (`window`, `card`, `button`, `text_input`, `slider`, `row`, `col`), themes (`modern-dark`, `glassmorphism`, `neo-brutalism`), custom CSS/JS styling, and state management.
- **`TerminX`**: Terminal UI and CLI script toolkit. ANSI colors, text styles, bordered boxes (`box`), tables (`table`), progress bars (`progress_bar`), screen/cursor controls, and interactive prompts.
- **`Xin`**: Mouse and keyboard input detection. `getch`, key polling, mouse position coordinates, click detection, and event listener dispatching.
- **`GameX`**: 2D & 3D game engine. Game loop, delta timing, AABB/circle physics collisions, and loaders for:
  - **2D Sprites**: `PNG`, `PSD`, `TGA`, `WebP`, `GIF`, `SVG`, `DDS`, `JSON`, `JPEG`, `ASEPRITE`.
  - **3D Models**: `FBX`, `OBJ`, `GLTF`/`GLB`, `BLEND`, `MAX`, `MAYA`, `USD`/`USDA`, `3DS`, `COLLADA` (`DAE`), `STL`.
- **`Xanmin8`**: Mathematical animation suite (Manim counterpart). Vector MObjects (`Circle`, `Square`, `Line`, `Text`, `MathTex`), animations (`Create`, `FadeIn`, `FadeOut`, `Transform`), scenes, and timeline rendering.

### System & Python Counterpart Libraries
Complete standard XPP counterparts for:
- `os`, `sys`, `pathlib`, `shutil`, `time`, `datetime`, `random`, `json`, `csv`, `re`, `collections`, `itertools`, `functools`, `urllib`, `http`, `socket`, `unittest`, `logging`, `sqlite3`.

---

## 3. Native Bridge & RNM Execution

Standard libraries and packages are automatically resolved across all five execution engines:
- **`RNM=ZITR`**: Native stack VM (runs with auto-injected native routines).
- **`RNM=ZCOM`**: Native bytecode compiler (`.xbc`).
- **`RNM=ZJIT`**: Native AOT compiler (with graceful portable VM fallback when system C++ compiler is not present).
- **`RNM=XCOM`**: Strict Python bytecode compiler.
- **`RNM=XITR`**: Python runtime VM.
