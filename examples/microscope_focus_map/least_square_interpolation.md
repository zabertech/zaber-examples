# Least Square Interpolation

This article explains the math behind the example code for focus map.  We will start with the simplest case of fitting a plane, then extend the idea to doing bilinear and higher order interpolation.

## Fitting a Plane with 3 points

Assume we have a number of points on the plane with coordinates $(x, y, z)$, where $x$ and $y$ are the Cartesian coordinates of the position of the microscope slide and $z$ is the focus height. The goal is to find the equation of a plane given the position of these points.

The equation of the plane is $ax + by + c = z$.

Since there are three unknown coefficients ($a$, $b$, and $c$), we would need three equations to solve for the unknowns.  This is the same as saying if we have three points $(x_p, y_p, z_p)$, with $p=0,1,2$, we can deterministically define the plane (assuming the three points form a triangle instead of a line).

$$
    ax_0 + by_0 + c = z_0
$$

$$
    ax_1 + by_1 + c = z_1
$$

$$
    ax_2 + by_2 + c = z_2
$$

We can rewrite the above in matrix form:

$$
    \begin{bmatrix}
        x_0 & y_0 & 1\\
        x_1 & y_1 & 1\\
        x_2 & y_2 & 1
    \end{bmatrix}
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    =
    \begin{bmatrix}
        z_0\\
        z_1\\
        z_2\\
    \end{bmatrix}
$$

In other words, we have:

$$
    A
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    =
    B
$$

To solve for the constants, multiply both sides by the inverse matrix $A^{-1}$

$$
    A^{-1}
    A
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    =
    A^{-1}
    B
$$

$$
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    =
    A^{-1}
    B
$$

## Fitting a Plane with more than 3 points

The above example works well if we have exactly 3 points to fit a plane, which has 3 degrees of freedom.  If we have more than 3 points, then we would want to find a best-fit plane using a least-square fit.  Extending the above example to have p-points:

$$
    \begin{bmatrix}
        x_0 & y_0 & 1\\
        x_1 & y_1 & 1\\
        \vdots & \vdots & \vdots\\
        x_p & y_p & 1
    \end{bmatrix}
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    =
    \begin{bmatrix}
        z_0\\
        z_1\\
        \vdots\\
        z_p
    \end{bmatrix}
$$

Now the system is over-determined, the formula to calculate the coefficients for a least-square best-fit is to use the left [pseudoinverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) $A^+ = (A^TA)^{-1}A^T$:

$$
    A^+
    A
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    =
    A^+
    B
$$

$$
    \begin{bmatrix}
        a\\
        b\\
        c
    \end{bmatrix}
    = (A^TA)^{-1}A^TB
$$

Reference: [Best Fitting Plane Given a Set of Points on Stackexchange](https://math.stackexchange.com/questions/99299/best-fitting-plane-given-a-set-of-points#answer-2306029)

## Bilinear Interpolation

The example above to fit a plane can be easily extended to the case of Bilinear Interpolation.  Bilinear Interpolation is like a plane, but with 4 points instead of 3.  As a result it is more akin to having a warped plane or stretched fabric pinned at four corners.

Reference: [Bilinear Interpolation on Wikipedia](https://en.wikipedia.org/wiki/Bilinear_interpolation)

If we were to rewrite the formula of the Plane and formula of Bilinear Interpolation side-by-side, they would look very similar, except Bilinear Interpolation has an extra term.

Plane:

$$
    f(x,y) = a_{00} + a_{10}x + a_{01}y = z
$$

Bilinear:

$$
    f(x,y) = a_{00} + a_{10}x + a_{01}y + a_{11}xy = z
$$

Note that we renamed the constants as $a_{ij}$, where $i$ is the order of $x$ and $j$ is the order of $y$. This is a more useful nomenclature than $a, b, c$ when we extend the algorithm to higher order interpolation later in the article.

There are 4 coefficients needed to describe a Bilinear interpolation.  In a similar way to the Plane, we can express the Bilinear interpolation in matrix form:

$$
    \begin{bmatrix}
        1 & x_0 & y_0 & x_0y_0\\
        1 & x_1 & y_1 & x_1y_1\\
        \vdots & \vdots & \vdots & \vdots \\
        1 & x_p & y_p & x_py_p
    \end{bmatrix}
    \begin{bmatrix}
        a_{00}\\
        a_{10}\\
        a_{01}\\
        a_{11}
    \end{bmatrix}
    =
    \begin{bmatrix}
        z_0\\
        z_1\\
        \vdots\\
        z_p
    \end{bmatrix}
$$

To solve for the coefficients, apply the same least-square technique:

$$
    \begin{bmatrix}
        a_{00}\\
        a_{10}\\
        a_{01}\\
        a_{11}
    \end{bmatrix}
    = (A^TA)^{-1}A^TB
$$

## Higher Order Interpolation

Reference: [Bicubic Interpolation on Wikipedia](https://en.wikipedia.org/wiki/Bicubic_interpolation)

Extending the Bilinear example to higher order, we can write a generic equation of $n^{th}$ order interpolation as follows:

$$
    f(x,y) = \sum_{i=0}^{n} \sum_{j=0}^{n} a_{ij} x^iy^j
$$

Expanded, for n=1 this becomes the formula for Bilinear Interpolation:

$$
    f(x,y) = a_{00} + a_{10}x + a_{01}y + a_{11}xy
$$

### Biquadratic Interpolation

For n=2, this becomes the formula for Biquadratic Interpolation:

$$
    f(x,y) = a_{00} + a_{10}x + a_{20}x^2
    + a_{01}y + a_{11}xy + a_{21}x^2y
    + a_{02}y^2 + a_{12}xy^2 + a_{22}x^2y^2
$$

Another way to write this in matrix form is:

$$
    f(x,y) =
    \begin{bmatrix}
        1 & x & x^2
    \end{bmatrix}
    \begin{bmatrix}
        a_{00} & a_{01} & a_{02}\\
        a_{10} & a_{11} & a_{12}\\
        a_{20} & a_{21} & a_{22}
    \end{bmatrix}
    \begin{bmatrix}
        1\\
        y\\
        y^2
    \end{bmatrix}
$$

This equation has 9 unknown coefficients, requiring a minimum of 9 points to fully determine the surface.  Expanding the formula needed to solve for the 9 coefficients:

$$
    \begin{bmatrix}
        1 & x_0 & x_0^2 & y_0 & x_0y_0 & x_0^2y_0 & y_0^2 & x_0y_0^2 & x_0^2y_0^2\\
        1 & x_1 & x_1^2 & y_1 & x_1y_1 & x_1^2y_1 & y_1^2 & x_1y_1^2 & x_1^2y_1^2\\
        \vdots & \vdots & \vdots & \vdots & \vdots & \vdots & \vdots & \vdots & \vdots\\
        1 & x_p & x_p^2 & y_p & x_py_p & x_p^2y_p & y_p^2 & x_py_p^2 & x_p^2y_p^2\\
    \end{bmatrix}
    \begin{bmatrix}
        a_{00}\\
        a_{10}\\
        a_{20}\\
        a_{01}\\
        a_{11}\\
        a_{21}\\
        a_{02}\\
        a_{12}\\
        a_{22}
    \end{bmatrix}
    =
    \begin{bmatrix}
        z_0\\
        z_1\\
        \vdots\\
        z_p
    \end{bmatrix}
$$

In other words, we have:

$$
    A
    \begin{bmatrix}
        a_{00}\\
        \vdots\\
        a_{22}
    \end{bmatrix}
    =
    B
$$

To solve for the coefficients, apply the same least-square technique:

$$
    \begin{bmatrix}
        a_{00}\\
        \vdots\\
        a_{22}
    \end{bmatrix}
    = (A^TA)^{-1}A^TB
$$

### Bicubic and higher order interpolation

Bicubic Interpolation is simply extending the above to n=3, and the interpolation formula has 4 x 4 = 16 coefficients.

$$
    f(x,y) =
    \begin{bmatrix}
        1 & x & x^2 & x^3
    \end{bmatrix}
    \begin{bmatrix}
        a_{00} & a_{01} & a_{02} & a_{03}\\
        a_{10} & a_{11} & a_{12} & a_{13}\\
        a_{20} & a_{21} & a_{22} & a_{23}\\
        a_{30} & a_{31} & a_{32} & a_{33}\\
    \end{bmatrix}
    \begin{bmatrix}
        1\\
        y\\
        y^2\\
        y^3
    \end{bmatrix}
$$

A minimum of 16 points is required to fully determine a bicubic surface.
To solve for the coefficients, apply the same least-square technique.

The above technique can be applied to any higher order polynomial interpolation.  The algorithm in [focus_map.py](focus_map.py) is written to handle any order of interpolation from bilinear (n=1) and up.
