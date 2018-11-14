
"""
It's not worth the trouble (it seems) to create bona-fide Plotly presentations
as a way of showing multiple plots (in serial, not subplot, format).
The end quality seems pretty bad and you are forced to do everything online.
Thus, just generating multiple html files seems preferable.
"""
import plotly.presentation_objs as pres # type: ignore
import plotly.plotly as py  # type: ignore
from plotly.graph_objs import Figure,Bar,Scatter # type: ignore

trace1 = Scatter(x=[0, 1],y=[0, 0.5])
trace2 = Scatter(x=[0, 1],y=[0, -0.5])
trace3 = Scatter(x=[0, 1],y=[0, 1])
trace4 = Bar(x=['cats', 'dogs'],y=[2, 2.1])
trace5 = Bar(x=['rats', 'cats'],y=[1, 5])
datas  = [[trace1], [trace2], [trace3], [trace4],[trace5]]
figs   = [Figure(data=data,layout={'autosize':True}) for data in datas]

plot_urls = [py.plot(fig,filename='temp%d'%i,auto_open=False) for i,fig in enumerate(figs)]

print('plot_urls ',plot_urls)

markdown_string = """
# slide 1
There is only one slide.
Plotly(https://plot.ly/~ksb_stanford/100)
---
# slide 2
Again, another slide on this page.
Plotly(https://plot.ly/~ksb_stanford/102)
---
# slide 2
Again, another slide on this page.
Plotly(https://plot.ly/~ksb_stanford/104)
---
# slide 2
Again, another slide on this page.
Plotly(https://plot.ly/~ksb_stanford/106)
---
# slide 2
Again, another slide on this page.
Plotly(https://plot.ly/~ksb_stanford/108)
"""

my_pres = pres.Presentation(markdown_string)
pres_url_1 = py.presentation_ops.upload(my_pres, 'pres-with-plotly-chart')
