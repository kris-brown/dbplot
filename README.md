# db plot
### work in progress

## Goal
Flexible interface between user-defined post-processing functions and SQL
databases. You should be able to generate Bar, Scatter, Line plots as well as
histograms by simply giving a query and specifying which functions to apply to
which query outputs. `matplotlib` is used in the backend to draw the graphs,
though we'll eventually switch to Plotly.
