import html
import io
import os
import re
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt
import requests

st.set_page_config(page_title="HR RKA 2027", page_icon="💰", layout="wide")

# =====================================================================
#  KONSTANTA & GAYA
# =====================================================================
TAHAP = ["PR Submit", "Approval", "AP", "Finance", "Paid"]
BULAN_PENDEK = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
NAMA_BULAN = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7,
              "agu": 8, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12}
ABAIKAN = {"idr", "usd", "description", "total", "no.", "no", "month", "desc", "budget",
           "realization", "remaining", "skk migas", "internal"}

BG, TXT, GRID = "#0e1a2b", "#cfd9ea", "#1f3350"

# Logo Prima Energy (dipakai untuk PEB dan PENN, disematkan langsung di kode)
LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAAXEAAACCCAMAAACHKAiVAAAASFBMVEX//////v////v+/v77///9/vv4//7x//79/f3+/Pj5/Pvw/P34+fjo9/vI3+uXssNbe5EhT24VRmoJRnMWQmMMQ24RPFwMNFGg+4yNAAAxsElEQVR42u19CXujOrAsRgtCCNsQwP//n76uaonFS5Y5Sb777g0zZ85MQmxcNK1eqktVxcNYW9d129Zt6rrLpWu6zvMIwTmTj+rv+L7DZsTbGH1/XS7nznd9430UwOs/xH8E8UDABfGmud5u18u58bDz6Fzrgh5/MH0r4kYRb2MviE+35Xrpe7Hy6MTV/CH+/YcRwB0wd5aIL8syXM9903QJkJ8Eb/Eq4lnE/fyh9R2H4C1YGkGXXmVaxhFmLph3MaW2DeEUosCNxfTPn3+HiW+Ih04QH8Z5HsXQiXlyp5RiUsTl1x9c/+1wOBAXhmzjQFxMfB6HCa5FltCYbAjJVvQsf8d/9ye1RuJi5Eb8uCL+9jbPwPx2gzvvfNN5m4IJEtHUf6j/ZxtvHYIUZ2Djirg4FWIuruU20bX0HdMhnFj/gfbfvcoj4m96COQTXItALqGiIv4XJf63Q5IcZDltbeyK+DIBbCIurkXs/AbX0gjkOxv/cy7/eHQ+9r6TYCR6X7WpTZ1k+SPdylvGXMz8Nlzgzn2KLiVZRkMVUgx/oP/LcZZ0vu99lWRttG1dA/HbMo3j2w7yRX6La+maPuHeyH+SDsU/9/JPxwXxX9N1yG4sa1n+cl0YHxbI3+ZlHBC1iDuXqMWGWBkJFGni5g/2rx5XllA6ORpBPKXa+f4smC+rlWvcMowaKcrzIH6lyrVE81dt+QfEc8wtqHvTCuJYI89XyX/GOR/qW0bWt87i+MWryE8S6z/E/wFxWReBZCOYVwhF4K6b/nIdxnEF/G1QzBdE51GWTWRD4S9k+UfEBUjkOX3TpVb8SvLiYvriWuY1ahHMJWqZ5IGwRhCXoPIzaJ/kF//gX/4ORXycB+aWcOfiMEyKthFDJ+bDMVIcZ9S3+qYR14Lirnm/QXQ6Hh/U0/SFLH995tQfe75+9OU1wVxkZVwGVmf7WDkJy8XUBXO4c3kGctyiTmaS4Lzvu5hc3dbfibjdHeZ/O+Jvb2K80ySYo4LSmZOsobHzjZi5xIXTtEP8bWQ+1AFyU4dvRPx/CiS/hDhKKHkJbRoT4imkJODDtUziz1fE5U8JFKerJE4xuPYP8X9FfNYaysRIsUHIfTJVkkQUmItrmXeIyw1ApUXi95i+FfHdGnv6v2DjMHO4EGDuA3L51qB6Iphfxx3iuDULi1s2RtN+G+JfOfd/BeJEUoKRBen8WWxbFs8kQXeMXX8e9EFYQ8WR62zTGZOq77q6/4OIa+On5DlN06eYjMTdPdr7c1k418K5RCxdNOkzV3fnevA38+IUYx4Rf3x5U73wZub/M8QzqlpCOcOJh5BM1xHxPeDw5tNwlqgGuaf55Ccoh3IxNiD1S/kw2Y9vn9psXJkN5/X0w23U883nQX2Fq9E3/QnY7xBXNGUFVb4KCoXGi40vy/x2RFwgv/ZN/BTizz/m+nEV8DsAtttzfDr0JHOPuJ75/In4OuJ6RZX5LcRpwmi2gQeXjH2GuPiV23DGLXmFuHn4UGZFKdtusUn9KjOfkgHtrD6Tk8zhBfn1DXECjh4JqsifQMmEh4fkAfBgzE8w0V4gjjxnQT3cJ2dzs/mI+Nuw3C4dmp8vEH+023sUg0Jevuz9PuvMX4xxfZXjLcSfK2Dql+RcE8IXEX92ekE8/CbiaLZdegFBnq3k5axxBXxejfwqJ5gXiKvRbUa9c9YxxrD7TvmaPxzh2XGw8f2CsL5IDOaLiD/5gfVef8VlfjUDujNgMXJBXBJ+rEPJXm/L8vaA+CJr52vEec3xcICN7lxA566gnsGSf7Ipsh753Hi8Q7vFN38xI67fZkBbfQ/i65v+HOL3Ro7wz6cKuZC5iAtZK7fzGr4P5w6O/MknrOUzCW62/L4/5POkljxpQwaBGHiD4/FMa9e749qapTNZzlPs5Gwb8BV1AnxEmk5t3OxqkfePngIeI1yXvHrQD3DanSHXG8H3k7OC1qRP39gIeOVV3t7oVaKJVepZ0rrdlnnex5ASuF8aOvKdL9S/1G0dxGT7/nzGb/lvd/TkSaMaL0ltlCQqJYlDj+fszgU3SQAWCwavxtHft67DNxuLknFlLRYbj1fo5OEAkqaKLfl99R2hyTmDR0fer+PpXZfkhSumAUjCKrnBje/43b7rKzyPRhbyqq6/DfH5BeJjRhwfoENFaxhQtlUzp1cXxGnjh6gYVdfKAHHcpufH5QK4BGoTUgBlIzZ4+WG48s9ybOd2tutCAnnMBVhgG+V8pMYg0MgbRvlin78U8VyQhfMM8bp2SQy46/X0HvM3yW2Zl8GC0uC78tbklSSP0Mn8IuJyDXiCO1Zup2FcK1rzdJO08ynisPHYnIfbgoLkjceS/y9/mwZg01divRW8C4aPSFpfT7ndn9uhcI/Gt4OPqs5XOXW4dGgTyuIuPqLBlxb5Ehq2VlAE3u7Bq9Ryg2OSB+IiF4d6XKeOaEVcPFwjxoKVS76LWkctX/1VGzdRPkEvnqXJlds5e/R5vl36O69yQPyyTPA9cpemaUL5gP+TR2UChZQVsy4p4j28G04Z8O1xkLOGEQfuwoJzAQ09BdYHLCzDIuGrS62E8BXs8rLcJHO7YmwME0w1IH+sJuAWoa0IwMWALnjZakPcBIc1vL9MfDFZp1Jqw4kZwe95Fbl8sS4be1ZuYXeZzILw8F3EJ9yZmca7HoBe8AQ9HZWZHp649WKg89ugNyUfeuaMcxdt9fWponOWRe0i9xELjfhgjG3IXWguYpXTcBt6XYBTSwu3j4iLD4MN4y2WixdzqopXkSXYtSk1cj/EsHBLmya2HFgw9jcRj2BLnMQaO23ECeQr4j6+RFyuG4nqcHeIHQNN+cuN0VCCYxDEuTwM0+5E2Pw4kVeNvhM6gqBIOieIyzVMePtkxCsjvBDEp3EZxWzPxLwgbh4R950AfsPtVMRXr5IRx7jfKAvWSCPneFT4bcSDvGd7QhVRHrjrJJ/tfcSNnC+ucpIgfhQvfMmRx4XHlTcNzgZul14l9rDxWTz2/XFlq3WC8cKxePKA8figL8IL7BpJ7GVlFR+G0Y5hIPna4s48QVyW32R7OiUase/k861ehU7Fw8TVpCQ06FNhHv844vOGeERycWpDyryKgYEik84uavL3YOORsICw2De7Q35eojgswlgQpquGGw3ppXAzPLp+O3Ay/JhYNBx0zIgPOF+8EuJwewpWPAGfPPFhLMF5HV8Kh0kxhPTJYF2kY5S1nzZuslcxsmjJzceiMohTQXVJcjwgnmqJGn8TcdsnhM3ywBFycS0TB1eyjT9HPAFxDBNxFLfk8Bl3xveaZcGrAPFp5EKmSVBTzpZ1UN4O7v+GfGtFHJQxIG4z4lg5x7VwL/FKov89zOYxLZWoVUx8Uk7Icoe4E1/YNfj2oI85lppExMOv2rhPPvUBtAqyntW1LLfpk4jTjPFoOk32vUSbAuNtgEHiu2GHOCF1UccI6HQ91jm5vcsl23jtnyOuzVrxeWR3OPqCPeJymXApng8Iw63bHnFxTrV8G+8mJwxvwzyyCdBH0OvD6fcQlw91hnn1yM4FDOt7GqnEeNeu+wTiGbz1cKAJYF3FDOMZbWxB/JYR11NqV+eTcW4vaI4LIyOO9O4QZ4ZW7RHHiZKr8t4cbNwgt5dPIYhiPUa5oiAeMuK4wR0uW5aNC+da8aaNxOQxfBcV4WPEjSwuV3wG6COI7aFYBGd3vl4/snExlb2NizvI/0PlgB98wWeW9AXxuFhUQRwDXoaYy0on6EmcOWksKm93QNwhPKx2XmXCTEeOgVq3Q5yAR3GKuLnLLAvnPBevgs+AZVPSUcnb5Nt4fMW5DAhhMUdch19EXPI3f70x72s6VucS+Ik9EqLLB4jPb1w5/epTUHqqJdaSrApppoTE8phAdgF9vaV4lboOedhR3ggZzXmY1ZEzNDIb4hLNY3GEq8PKiVBFghh5IY3q5IG0++pxFFNBnILgFDS0snIC8hPGnJw4ecSNyDdl+ZAYiQtx78zpZ73KfPAqqNbmmbcOyyd+IzPv4Ww+QHxGb67xkrdoJZBBGH053CkQ7zfERyAekW8EnowFVwtiA1im4MiEjPiAMOgixifBfMmAEO1cB9D25FSNI91m41o+Vxyn+XplQlsQF0cNxOX+ionjxiE5kzRr4eIpuddv2LjWDmuxcfEqN3Y+QfGEndf0ryhoN124Qxyz+0S8U8Rp40gUrdZe5ZQ2RBd6+Ww3SW2uCOUaxuNAnDleq7VXVKPkYUAd7SqZ1A2tbIb/sHHge5WUqN15FQmfLvDCkmPBr2yI17VrWXuVtGwZyPeT8H1Y1I9zgrg2slxLxnHRSJSVHASRiGAR+chH3OhL/wX99zMgG8VPyodWzjO5oNBdibViLqB7Vpf3rV9LIQsXNMqiH+dibwk4ZnDl48WQPBFn3pgy4vKQp7K6Wk7gcTBJHNjwNmsOFF1GHNIB1x6pVhQXbBt6lUEcDaKeGbmV+BVx8vFkMAWPBSHEJA/WjfPvZyRMQFziUEXctWiKyEVN6pX4FE7i7EdUj1JrvonR91nERzKxFHNwnrmqxZgby/uc01Ie54A4HbI2jV0eka4K4sOKOAolTUbcxZQYriTjJQG4IJJDuhQtPOqGuHVA3BTEkRSdSdCGC5J0tqKNG7xnquSDYLkeJ3klcRljrqtEqG7UzHwl/UcJC77bS+TOu8eXkteqfg9xehVBfGF5g+MUnXxU5nSZs/AB4gw/DCdGdShdbiM8JlBbEWes4vXuiCEDhxqrLWY2GB0CcY/U/QHxYuNcTHum+/SJyRmswIbvKXkcw8x5IR0bTnpeEQcXXiJHlMOmgQG93HKJpwa9LBh59ZLB9FOIc0YClVQVXoGdQ9Hps4i3dSgSAHVrNLWbidqKOOJxku+QI3kmSx0iFYnTYL7gFkR4FXOHuC02PowjVjzJzuSBkbBOIEf7TGP7CqE2aoK4dUD8tmg8rog767WkOIwsmyM48HKH+BzCnaFm+8uIyyqI3s+SZ94kqqAZftKrFMTxI3zAuwthvMoTG9e6StOVWkD+f9+wjoPVbIDaC1uej17Fq1dBfCU/IOcvI1c/3jbe8FNkCoBEkoNmgvi8IQ7AZYVGwKrlhIhUgD+xYIElq147zb+G+Bo2ZtfSIx3Cw/gJxL3G2AXwmGyHDzPn+EwRl9hdnvZzf6hioY51XRi443Z0spw+2vgOcTwHeGME5eSipoz4KfQowgri7BPBUS0F8ZY+Rx4BRo7gmmlZRhBHq2iaWCru7Pf09j+F+LH/XGjmHef0P0BcMyA0HZX14FDLRjkMWf4Ml2lXxCWSvC/VXpHR3DIOvVyPoHOqHhC3ivg4sqTCjhIemTPZqqxpwcSRAIi7uXKUUvzHijiCJ98xMuStxdAq2q8JRTuE7/JOfRN+A3EvoTdM8o6BmyPFznJofE+fyIijD9sRloUpTi4FdjxQCWsQFciLoN7rAxHPcxpoE+UmEI55Idn3xqZjx7TQFa+yFMRLzklWk1gj/TEjT2bJrUtAnCXIgUUXCUsuE228UcSxbMLEb4M6HfEq6E3gLsgtQPwuwUKSmNb8Z87Qx4ibBMSHbc6QbfyBlGcf+vAu4sNyVx9HnNORGoBWJ+qBvcQTBfG59N3YHh3wjuwDUYmh90ZbQB8gbqPXloPWbWGrwaB3ydYm+k6yVgPJcUW8FT/XYDBhmOHFe5iIqTweBt6nSYPNWKXwC4i7GBpax44hpFPjgnn3gY3TZO4PuIsJQQGb6aneED82OueBogByb1nbECPjRKMLzSPizYo4SwP9deAaqD0cljvPyDUnOHrxcv6IeM3IcJBruI2X/niwtsuyZkq/hHgbZZWDfYyrtpC2JG+l6/YacUY2xwPdenpmnSZiWK9+/I1JVulADwtbX/LjYt8edcuUq+zufcS7kBLDkpEECDZS4MXkEyB9h2/LiM+rjQc6/+ntofMn/xo433dFWdn8CuK13No88jZpryoPBfH678i1d4gzUyUBQlHM/4MHH1TGstsQF1+1vzHTNN/w+c+0705cSmJx4RFxaw6IewPlAE3np2sj/hh9PKyA8lxJjtUjyt8hzuwZJs6ADK3w8pQNIAxgIoe8V/HiQSnTP454G3p2N4eFzdt5HUcs7ImXiM+kRCxjPrDmjiNqpezmZ8Az4guihHOJDjFhh3IqW5/IiWJy1QsbR89k71VOJ0npEXiABX9OKPjCiQ+c/RUD4kT2irjVshz89fims3ybYSx5zA/J8RklT/mt/PaftXE4RhTwEOaKza7zV68QR7HOEHFtypTVkCwhEK8kPRxU8axvU0Zce0C9hjXECLUmxGoRjiG2W+/uwauEPeIcpWFcJ68gfiXl4OWGego6FeCYrYg3gfIPjOGVI7+uJWQhTfpYs0fRgCytca79fsRzZYI1nsCGKwUpbjtJJ4Zfx7ygEI5rozb+9rbsGCh4XJVQqMxDhC4SYUskUeoqHbNEBpL9RW8wm88uqUtpQ810vCCOlECyQCZFGo+Ly5YvwpXjlg0oivC1pkWTKAnxUNstiFtUGOUeIFidR17EpIQ8JgHZ3PFcL5MsAVrbFHv6OcSdIM7MVgynU3GEqegLkT0R7hBH+QEtw4w4+Cr3B2mrqH8zmXcSq3T04+gBaWMZ8ZsnFW1kLNz1TG/xLZR9uw3xSMTboD0gIq7c50hWCuu2+rxoatPxAr3fEMerMpyUC3hCmNFMjNPxWHVdyoShH0U8U/L4MIp/5QDiOiTxYON7xCedzyqReP7LSiL3B8TZddMGnfU2df580ZYjGjLyBXX5tTnYuCAezcndIc4iOqh1E6MMUrAYp/ToMJ12iEtC3SaPIuFtZClGCTM8dhHipC6r0T5HbX4YcTBtTmAeAPKekSK92/AE8bYQEQ4558pUUSctax3KQtqIC3XcI+4y4rZTX04xV/qKqKqiWihcEY9PEJebKPGe7yTAYjVcgibmPmyg7BEnJwsL65UaG8Olbx4GBxpSbfFtrY3VP444IIicUIAaInGQ/AWFiyeIG9Y0d4ijdUzNBKejDsbFtqKiuSEV3Etco4i/EXEauQMryTI1RYrNiEVuFN8KfOYNcXQdBHEI1W+Is/oKI9fVl/XWzCv1cCpHxCWzzBQvBvMNKi3rgdpx0hOwEoArbTio8bOIoy8gKyKed3EtUKRgdL6MrxA3awY0gfBhwxpn1PXKpJAF86SRZOs3G6eRg8sJb81W4zKwDihPio0JzYU7xGOsSjyeESdfoD0xRJFVD5HdwhSmk89wAvmqrJyL+PEGNcObdq4lrXSmTplgI7eXF0qqx2rk9j8ONH8CcbnToNfq27OZgPEHyA49xiqwb4bjivhEhpA1dQnsnPZb9OC5sPFdZ1m8jCMLCaM4FixYCSuxYkBuUdwKEDf+BeIaqzjGVy3iK4SII5Ia7UJUcAing1cB4vIozPoQSESkffO1h4Jg3aWedVCBBOGw/SnExxXxFM9n+fAJ7VlsNRFRVCOt+dr3zxFHNU79+IQQLqyAOxeMzhQixpCnE4LQngyhWZem4HQQAiOdXqcV2LcRcHwlaIqT9ryZQBylQWRA9CoTEcdDUrNxF8jMR7yUHxIQbThdpzaOcroEpixhzUygqVmKgBt1fENPivRIMlLQO8RFgjKjkP8o4p3XmRh2olKISUnvlyu5tRqM5Zfj7JKtHPImUByGhUOfZe64vKsyEEjYNnhsG+34DiRomZy44j6RObEg89ZWmMuzV5eB7CIWY+VxSAxfiHivXqV2JzSlSQUfB1bXPSM7yPDQxYO1ooiTGg16vn6YuBs9xzOJqg2L/QvTICL+E+yJI+KqdIMtDkKl0p9wfxdW6vY2fqLcFfgqSoAdNFWzwawKWOsUrCIuJq1TKWy1IJrAKAnPbMlC16YAFF18RvwUu7JEoHZZgUkEG0duiyuC5wruFI3tbcclB9T7zIQ2NSPHbuWrwHyXXEyPyqnJs/8Gs4cgz2kOjJT/JmkQET/9LOLkZLFE3VUoccDHMTrvKcGyY+yviCu9aeHoCCoB3BLheGAJs5YPrkeHUSlAnj0l3ho6Ua7T7MMMnhQ5eeajPzMxvID2GjHrFuloUG+HmrFyZWUR7yNH4AYFnIEdt3BgMMmEtOo8L1PcDkOUu4sE4oaIN+cBOazcI6vd5R9E3EMgW7ub4E9lY0Gf3Uelxe/dmlHEUwvjhGDoRdeaR8QrOCAiXvsuj55hblURJ8uEbGZa+Q2l4V7zvRCr/NLgOCTJ8YNEN3yF4WwTh16RJZsqgiYgjyKaDJ2qfleyFsgiY8+YaBrOFSgSGMeTc2KMZYevg5gDuXjsRUtUfLbK5PtpxG9oWU7qWrg2JV1BCfhBTADIVrROBu4wLxaVjfXWHAb0s7dmsRT5Je5on6hAbAuxRxLyjlY+gIyWM2wjKzcsFyAB8RiicdsrRJ8RD6eqTtxICj0IcXygF1q8bIUmEE+PPeaV4DS7vlIWGPdtIKa8UjT6nWWomWNdczI/i3hD3iFG/rgZVp+5simB/Aqe72HhNgVxRCCYALIR7gH4mvpwEHHmmAkzxGfubRYy4nDzGDAOiY3o8xmqRhlxjITj9J7cZ0mHjbxFbND6l6USA7KcHMeGOoZTnQIwJXZdBA+RsWu0fIVOTjf9hXXMLGhPJrXWNRgcMtYEcVUsSJ4Wa0nD/fcq+UeI17BxZcGBIJR3CaJPjKHY3GHwPftxSFSCbsIeC++KftZ7xBmrBNtp51l8gtkQr4A4+gueM7y69AniVdK6Y9MJnkjbxcblzlBJPYHBnHVWJJ3hDW0rieRTzKs3NbxTkrfEWJJJvc3TCCkDzqQSkOPHSZNUupAsn5L4ZhuHctQm+/KJ/UyKK3qF+EzEG9g4twia8iz+mCm2zAC59j++NmfddKRkXfvzZ32QvLFMisip4LmrkyoOiCosFAPRuW/vCi+ggbOQj19l9VWbJRbuh5QlBke5kFcQ11WEw0YNUrtVZsQWIZtMMdRLPnFDGbedpdov1gUXXBlFX61IXaJ5/KSnk/7xCcQlkfAkd2RFEEp/opfgDe79/Y0sggOMQYJ9Rxo1W3y+anxaW+Q3TqtOVi4GJ50NypNEBJb46tLg9FfUX1XWdq0r/mKemc3bFL0QBV0LJ3wprOtZUmdFHHfJ6IUiK9sApyVY/LpHPD+5j7a1MUQ/i/i49pTRHYEOOeer6/a5uErO5V24UwCqzMbBXi9SEV+N2hxsXI88swXInTa/GMjh1beXKcn54eAXGPrj3ev8/kUChxllZBiI1875QnEBNteI9OX1hoTMPaRXsaXxZXZW/tiT2wH+BcRXvcNR5fZJfurW+OOZ+XLwR70Gf+VLqrMRbqjwm3spsozQdriMtz47pbJ3Z15PEa8z4gQJdxfOABHIbh7MUT5Hx4Y2xFnDwcJZEFd/AteA77Iktl3m+vGeVAD+zcbfiu6NSquskeIzNp6i6R6Mzh393vZpCl6shhwQX2VRlLKZXzKWf9WH18+BxXGwrsAACt7hruwRd3lMoFSpCuL5qvTqQ9j00HTEeWclxTnys5tniOeg8kuIv60Ck6Rw0rU8QVzeNLtcLV8VG8+VLGdWY93fke3jw5Gae8TdDvGUotub6N3B0/jbtetp+pcN8d2tWScZi/CxLklmf0/Qqdr00lbBqZ3fo58vz+5xcTO1KcJb7tOIz0fEOTYJvskzG2ccWxa4HRLHddQWnrE5IM479IC4yWsmMgB29leUUHy6S2Z98EF+e261uNKZ1WWXa1GjgBWwOZJvzOFNM+Kq6hVMnmOyqvGlsnNhVWrM4Y/NLv3eybrAHF0AeY34+J6NU9NTS0l3OllY3Dl2Y8jrZBhXZsO3RhZ/Ye1lQFZhWtFBUqSSD2MwkO3SUbcQjlIwtx4bV+K3aTG1gjZS35VX7QqTFMM9zdo08+ABJCWBdHelBvJPJORJgnlSG5dcKeIPrevU0PPZXgqfR/+Qlwu4FAfp+5iUxQrM6eq2q0etzjC4RKXAVv+OOCU4LlAH2yNutB4iK05gvKzX2bw8fId9QOTzSrINI0me9lPpAnqHuHwc6gPJxSfJBpxL/PzN+0eHirJYKqbtdm+8a2SCjNMDurQrEYlRticTsXFjYaiuR74HYNOJyTuwd2lY1C+K2gHfIS6xrcltXps+hXi0d4jPOqJCIvtzxGvoZDXnTxx9RJ6ZJJsDHytnTKG6R7w2nE/seqVeRD7ctvvUO4CLkSrbv/o+tqwDYtEdq3InQ5YO9S8ul4POF8ljsCVM5zg+PhA6A6imfUQ8VMxvIYX2NRufV2lEmPiNBKh7xK06ldqiZzF8fFwvyDwiCtmgaaGlxzj7iDjGLQE4diq6Xs98fHMl9uM3YJHZP7+aLH5G1Ju4arwaLA6dSrJB42WYlnvxrvJjKEpG9sT4To01pJntETdVx+kaNHa+hLgmnZrtzzoYbO90a21GHLPzmHNadjzPhwPdaYnse4sx1jPV5km4B54PiIOLJT77gg+MhlRENQSSgCvDf+IrTkv5f34PHesBe0X10faH/nvK/N2uK+EfyrwgOBOlAacppX2k5FfWUMPNzNm3rCbgN/DyMWNaHxGHHABKjzjjM4jHjPi80vJAIEQdsfd3ZOYV8dqxoLxyPJ8dyKZ0+AGL6OWm2kxnzFBEHfe/R7xhr4ikjY4Gj3FXsvpfvwm7FL1O9AwjPlcmnc6lUkQuJKcmQZ8DQFjBraF84ICZGJ4174W+CD0YwtwFTC+FXGO5Adi4586ryBlnThRNn0FcPLLRSpZeJ69Rd3dHr/YR8YoTm9ouh24/nwj+ujso4IcOpA7mY55Nt2Hpoz9W3ZU04dmvwSjLmVVzdkfn1RSeHxNmA3vshyGYPD0Z8C2U/17FcquENYKUP/m9uzn5dgH2QW8V6vYc2sIABrp7vT14FQlsDR5H9DMg/VJpHfZVPO4j5+7EP4Dujec3T+rkaTcJjZ/KhuOnKFRCLt9HfrzjYP5tnmbIlmHgx1ftNlheaW1AYtqGiANDRPqlzz9+6Me9qnhwGO7+2wBNXnFQ7DpVd1WywgQ/B2JQJqdu82DX/INDHlvo2cRC4xTTzhyeC4zRtYqaR2JIiXmJuNbHbdRpVw755XdZBnV7DYce64e6ipJ+EKtkUsl5JXhuTM88nYJGQwTxUgVWKKQ0KOUYg/QaxiEu5l3EsMZAhYkzlG1CnrYE6/x8JJLexSoOxXqdPx6e8TgHfizyG5XKmdjxEZckGE6DMoELITHHLnkMjz4uT5LdyvYaaKgGLR9zyKinMtdADcGPEE9UkbAalfHqcmTky7Cvu9si4oC4Mj377kUsriEqWrdKWEH4uYxguPRISBzjXotlobL3iPNf14UDsY1ud/kiHmdvJyNeuJwluC5b2HFORrfcQZZZ9Xx8yj4mPbOARnNOPHkQWDurl8c6jhiS/C+oB6qajgIhfxMrJzlkUmaZ/wzikgSmjmlMDv8blQ6TR2Yr+T1FfJiwDZyqDz1CQmK+WIFxBXHM53JNPmN4Qh5wyXS0V2efI55BbBgIM9PcIZ1/eRJYmoI4uiklNRN8vYbcaKSOqqImCX8UH66zSjoSjxwpZ7Esqevnb8juvuI2IfElHXRQCkiHOgsqENAfQJiEgRgsWc2nbBzMbUtlD8/iQaPZLJAtg7EPE7QtZyTyp+j5k35N+UqyB/V+Itoq4tvw1ZVj2cgtHEt31SvEbxwXabL5aW0jtxe2Xg9+tFsRxza6Ppoi68/0nPJwOh8uD67Jo8rc6phDSE20FRsWrPfSQ2MIGJLClPqzKcj/oKzFeAvVJjbIkgFNVIe+uEJ9DnF2uFuQzRzLXyxG+LLXw2vE/WXAwA+sSougdzrkCfI/lmUmIg7OPIQ+KSd54fxELpYqPfE54oxcUGxyu3rwvnomzyJUQ7sV8Q5DgicStKlMERPDHhKBz1DfieoF6GUappbWZAX/UhNTQRI02eGhInVgyiANQyntyaaaHM0xF6Hk3lSfsnH0iR3V2biqpLDjcpjniNeK+EROlryP9vgeujMmd0QpBic+aLxeOBVCZicEwUrZ+iXiM4SsbKyfHJmtyUJHRnwG+8FG3SaaUwiJgwDgFU4YWgeBPapQMEXJgKmKg7ERuNV1AUUNy+Nyxn90yp5WVikHurgEkwSPgSa5D708rp+xcccQO7lc0NfWyB2L5gnimXQN35ibP8cOBQkYWqELTUdlOFnpr6DOqaZtk0c430F84d4KJm4Qu/bYEQqSvspbQh1IImtFPF8CL7tWU+wxQjMK4pZaWpwBugAjcd0Q0Tlxs5r6KCQIUYeIuV78aiHodcVTRyvreCtJ2oEEGG4fZ5lU42B+Jky2Wzm1/Mvq9IbZi/067ufyp2sWcnhy1DGoVzFEnJx5arSCB8g9tSLYXZgehJhVHUuIR8TDirhP7KSxMWDWvgSr3+IIq6Bk0kEZ7xyEyS0pa/OVwDwFh9u18RASBmV9GjC4K0uJagGeWL40bhu6y70on9WO2izQQiEB+P9YpBSgaoKhMsLwKcTXFQnth7bOiFcfI87xPMjrcdTgcK1t5uWrNMQOcZVTYVaCvDtRXzG9Rlz1ZnzpjGz9UIwDoY1hgbjzO8SplKay2inlh5+Iy7cFJ+SHlCyCYmis2XMDjZG8bmUAsPzLjwQJfqMfwqE+eFZJMRWQY1gPq2AqnT6NeFgB9zYHa7nR96GNMwtjQKmx975ppeXkButaa1fEuas2GaIDIccJKLW+QpwrZ7eTt7ivgDfKteKPqkolx72oTgeXTvdjBWXBATxOeaTIFYdV4o64tiAuztUysOk4upLr/tp4MbqW5pEhsh0wA0M5i5H7mfr8pH8KceaRvkSEB+2ie9TvbVxj3NycOe6EkoHpOwPr6FQyjGsV+IrkfzHj7y2GM18gXgbUunc6EmTkdkfEty6QCo7DddOPW0lexE5Vlhn2rBQmuvyk7Y/73AIhf69hDDRDuFCKwSAvY3LPSxSjIMnOfQZxLJIb/bu6Q/z0HuKo91zfbxd00cbgNxu3iVYuUQ5CbaaI0aTwGnH517tvAN4VCgYFcWRw235m2OiD0seMZKYzBMrPV6rrnNm3NCE/D4bTd9z8Zbf9C3N+uWKvi1ytJZRxyWJcpdiC5xm0R2c+hfi6zFhtOuwwN9W7iM+sZL17oChlifjbmAUPKeV/4zz/xN0z6ta89CrjR29ArcmaMqCK+MZ3C/rodkXfG4GmoHZGjZGpbCw63mxRS/L4fPcXCWryPEBynU6888UokTPp0GLfcYCPiL8QUc2VLLcn1QHgI+KPzIyMuFFNT7Sgl4PyxL4fwPqmpcA2EV+4+wnmRrUsSN02TBA6o12OB8SH3Sz3kwO0c4jK18mvWT76H7LO2pjpi+w73LDXwki9xUrO5AS8V2Zc9qcegJcJ8v075Bp/1l/zRYsYfY6c9veRc2QkPT7dn3M+IG7cO/sq3i+etY6fuFUJgftKlhbAoVcAJY2FcxHM/3Wy6QLxDdJys6r8jBpqVlbJ8fhUEG/OGtVMz5sRqr7APWySrpzIgM5Z/Oy81z5Du2GiXiqESnPYkhEvBQStx2NCrlTedX8RjKpwwIJypSgiswxGa6OEHUd3ts6NpHrDA+BsrU0Z8S/tr6WImxXx+W0H9DwdDkxqsrpMyJEBTWVzkpjlksQaxq16ayhyukecaROf4UOHobzdooGZahfSU8+PLmiAOBJyV8lzEfAxGdJ6QPRrxGCKHGJ+q7Egrrv2XrxubyZLfMdpMajjUCxiYsU8hh3i43jnUb4R8YmCNrdXB3dR6uHeNsQZREnGjOr3cqNAHzoFFrsq+Cc2nluaL99jooxQrWro/Fjq4PJdR6cTOyEMGFHhkEuSQDFXYKLbEYNtYkXxtvdY/BeEZmDjRNxalCYhj6P61qwlxxD2iKs40iPq34H4Mk7jczmHtX1AE79DHDWKhMnASXVluDcrm72PiI/T8N47sA8p6bUKaL/Ng25HhGYWMhWoj4y6FCC24O6H3aXUvBBarFNLUZbvZysnZS2AOIe0cGOyogB5VFcMlvv9vpMcUxwf9or8LhtnH7N7ZOVs2Qp5InvEI+tOXdLK0A3VQRZZGkk9m3vENZzxzXG3w61uywAaKaEtNl7aw9zhSWcQ8pb12G+IpRC8LJUqAvnPmeSmEwirVILmdPDZ+JQF8VPFxj0qYyMbWiCYHHdi21Rqjnv6fhPi8tpXdlri40HZGmYGmLTf+/HaNrZOvep93MZBR4778Gjjy6x7gT09YhbtwLB1zIiznHrLvAk41HnUJiIyxwSZ73JbC+Ibf7TFzl/6mokigp3O4Y0b4lUg9YuqvLd50HpvNHvmkadKzS1HE9+N+E3rKk3eELWwLAs3n9QU7JW0R5wEcUa3rJuiGKfGImfbfe2QXoXbPUvchYJK2S14exsqPFFeL+XOsrigK3qH4omu3GdppjhX43lfoBmKZt5t4m01KxVeXgjd1iqCrEeOnkaMTX4gNsQrtgGYcM+jSp3YA9Wry/ueUCBp3scs2IMWGdCXEM86WYa8w1Vh0jutTbj9TrLcj4C3J2f582rjUPto8wwc9l8CzYK1ITJUlqNXETs6bnW7I6vj3nmOjK59zp0q7hV7cs0jHHijKaNlEbjX0sgFhSxzIisdqT7629EabcW0wQZqpLGOQsSDzvoYdqCac0a8iea4g2KXU4BB1ZiKztt/QNzkXcYYHWpdpYmaKZvT7hfy0nwuqm7XBaT04lV8oeZTWWTmFsNwLM9sHDkUN0AokxOH8QBPnWJFPOecXaOZz/kKlW1VdNfuB26SaiGqVi2kVliKrd2u1pE54/llr3nl9NEUDr/lVpmKuISNx8kdfW+KjmVtvZ1X+e+IvyniXsnjx7YRK746+0mvMu/8+Io4RYsYkaBp/gJxKkBt3dMiShwcI+oMzZrlw3LRrocM5YRiG6lU3FslktiK1QItIMRRXVJSs9sHigq5Xl9GvNkjbu4QP1S2WaFO1LGH6vSIdEAj8u9BfC6Is9d7RJzqR2ZFPG8jrIhnERwsVJT4VdHkM6VQby8QzzsnH2OVMvm/Io6923Qb7FPiKy95Z1T4IKeaZnTkE3tANuV2z2FqD7TITyCuQf0R8RQqLAvYqILbWJWc6rsQ166bq4n4AXBxkEa1WNg+uUPcatsMirOq4KPCBSiOTY82zsm3bSzzsFe8Nvt2iKPNEAyGczGdjyIl4x0oZ2tu2HFzA20rdLlpkW28zOFh5o1bAOZKz3s27o7tspSCyt53XtXsbxTSf/sexMteKVg3H70KhU449BQU8WVDXK66zqRLEj6WG9OVK3dCeObHw35D9sO4zh3imBII3BG4Cn3WzV60RhnV+kk90sYfOJAuj8OViTaXAwC0lvI+iHd+/GDj4a5Bye0xKQaFEJPu/DZ/M+Jx3bgDQvvlV42N7mCRO8RvG+IVzTQmPP7JUk90UqbmI+Khjcm9OrTFvEMcCQyIPmBHU46JcQIdS4qgVASKrqJcT5JzyLPpu351IsMVTq8g/tqrhLsRcmw00mp3gnKuZ93wdM7SaHj+vqIqnxsUEvHplnSKOPbfi37tRa6TV9q2cm3OORVxxPLiVcrwNyIx3doD+9HqPqXXfZYviIMnlT2CzpRRCSj/Incz+X1HAhI7zsTUWSpgcSMhxo3K2VccsXbobjy87nVoi3inWAZasleBuMVTxBsIBj6AZPIsJYehGJ1Dizpr0YT2K8oKJg8sG0/+OFVMlTb3hHgIoQTEDvIca30ciHvqq5j9tpqwJW1g6a6a4kcM3gIxhUptPqkhbHKFfZLcBjvkaWcZWwNgsMogaohRN7mWewdfjijGJa+QT6zPc/d47E6euxOW81uZengmfQ7durCNJsNzZJ4BqM7pGYDan4c+k254OrCCdGHH6ms7JyDm5qgbdoUF2xS7/r57NPwgEIPT+vgRcfwjxLzf+jRhZ9g3poN17rrNTBrfnwMSFD2Froi4PLlQwTEUMKpTrww4cDRB7gLbx2mNG2JO01RUdrWZmgewsm496lgsxBPxHVLcH47aaaDXvkKc2UKTo3MQHRXxr8meZeqVq2jj09sjYfue3q0athCrmp4jjj3wKu1+Qul/QQuysU4ridz27iP+uPgZpt1Ma5ou5r2sGTjGIkRJHUuV3xPTAw8CHEIU+pZ1XuiBQa4Mc0kVFHFzQHxRqtBTAGsC7jTE4kZqF+6CA8SrrwmfKeImsJgzcgV+1XWjMnaeShEbhw7VhRs4VNuG1JyvxHweIadOMWM576g2e1MV3Xf6bpgDgsg7SksDe2lNMhviqeIuZuDTo2BrwI8BIbZrylb1AzayAP30tm4poqV9ZulgmN+0zrjb1CNAC2qgQHvXu2eQ55Q4pw6sjsn7geDqUv3F/Vgy4pRbY92CMzMM8++6YvonEhhsSUtpsmzjh+1u8EeqK82FirxcE7kYknLx3rCRvOgNO2lxx3bS6xufsvIobbyKaPvCysGKrRKnMxMF9/qzZuK5x6RDKEVLnXV13H5Snpu438ER4sPnQXewtbI0PEF8BzgSYxWn4u6b4unclyxcJQQMvQr548We19r09iWYC8pr2K3zPNFWoGbxgDiW9hS8alXd8CONIEMK7MKY4vWhMyyJiONHuXFElbVe4cfBvtV1Gc+OSaAhoxLisUkjMWeVr5jLMGgHddThHM67XRjL72flnenyaFvvbRWfIB5YCkLBobIgnYHXJdkeNhBMX0I860Y6iBBiv4+BEu9FYn/TfdddGtA/v8ICq2SxuwlbcOEJ4pXq/cEMLtQoU8k09exZUn566sXJXZBoPXFuhA0CIG4K4sgUUDMmRQZ+HNFoewqQCtWtQQE6ZyGODUNdUXWSltsO7SfQUsttENGilbj/6XrHwnImyp6M7teYKXzt122ceVAeMP5wohgzuJJ34JlC7+K56LHOAaMe3Wuw5pS79qk36JXlysvpUIEJRSLSaG5DbElXogS/zhieKlUQ4M8dZ5YL1P3K+opH4Xtu3pTpSfGoKPT/AC5X5vzDlsTEAAAAAElFTkSuQmCC"
HIJAU, KUNING, MERAH, BIRU = "#2ecc71", "#f5a623", "#ff5c5c", "#3aa0ff"

st.markdown(f"""<style>
.fm-card{{background:{BG};border:1px solid {GRID};border-radius:12px;padding:14px 16px;margin-bottom:12px;color:#e8eef7}}
.fm-top{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}}
.fm-name{{font-weight:700;font-size:1.02rem;color:#ffffff}}
.fm-line{{font-size:.75rem;color:#8fa3bf}}
.fm-bar{{height:10px;background:#1b2b44;border-radius:6px;overflow:hidden;margin:6px 0 4px 0}}
.fm-fill{{height:100%;border-radius:6px}}
.fm-pct{{font-size:.78rem;color:#8fa3bf;margin-bottom:8px}}
.fm-row{{display:flex;justify-content:space-between;font-size:.88rem;padding:2px 0;color:#b8c7dd}}
.fm-row b{{color:#ffffff}}
.fm-row b.pos{{color:{HIJAU}}}
.fm-row b.neg{{color:{MERAH}}}
.fm-row b.mut{{color:#8fa3bf;font-weight:400}}
.logo-box{{background:#ffffff;border-radius:10px;padding:8px 12px;display:inline-block}}
.logo-box img{{height:56px;display:block}}
.pay-card{{background:{BG};border:1px solid {GRID};border-radius:12px;padding:12px 14px;margin-bottom:12px;color:#e8eef7}}
.pay-head{{display:flex;justify-content:space-between;align-items:baseline;gap:8px}}
.pay-title{{font-weight:700;color:#ffffff;font-size:.98rem}}
.pay-badge{{font-size:.75rem;color:{KUNING};white-space:nowrap}}
.pay-doc{{font-size:.8rem;color:#8fa3bf;margin-top:2px}}
.pay-doc b{{color:#e8eef7}}
.pay-amt{{font-size:.88rem;color:#b8c7dd;margin:6px 0 8px 0}}
.pay-amt b{{color:#ffffff}}
.chips{{display:flex;gap:5px;flex-wrap:wrap}}
.chip{{flex:1;min-width:64px;border-radius:8px;padding:5px 6px;font-size:.7rem;text-align:center}}
.chip small{{display:block;font-size:.68rem}}
.chip.on{{background:#10331f;border:1px solid {HIJAU};color:#bff5d3}}
.chip.on small{{color:#ffffff}}
.chip.off{{background:#16233a;border:1px solid #223756;color:#6f86a6}}
</style>""", unsafe_allow_html=True)


def usd(x):
    return f"USD {x:,.0f}"


def idr(x):
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def gaya(chart, judul=None, tinggi=320):
    """Beri tampilan gelap ala Football Manager pada grafik."""
    if judul:
        chart = chart.properties(title=judul)
    return (chart.properties(height=tinggi, padding={"left": 12, "top": 12, "right": 12, "bottom": 12})
            .configure(background=BG)
            .configure_axis(labelColor=TXT, titleColor=TXT, gridColor=GRID, domainColor=GRID, tickColor=GRID)
            .configure_legend(labelColor=TXT, titleColor=TXT, orient="bottom")
            .configure_title(color="#ffffff", anchor="start", fontSize=14)
            .configure_view(stroke=None))


# =====================================================================
#  FUNGSI MEMBACA EXCEL
# =====================================================================
def kosong(x):
    try:
        if pd.isna(x):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(x, str):
        s = x.strip()
        return s == "" or s.startswith("#")
    return False


def angka(x):
    if kosong(x):
        return 0.0
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if pd.isna(v) else v


def teks_dok(x):
    if kosong(x):
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()


def parse_bulan(x):
    if not isinstance(x, str):
        return None
    t = x.strip().lower()
    m = re.search(r"(20\d\d)", t)
    bln = NAMA_BULAN.get(t[:3])
    if m and bln:
        return pd.Timestamp(int(m.group(1)), bln, 1)
    return None


def baca_tanggal(x):
    """Kembalikan (tanggal atau None, teks untuk ditampilkan)."""
    if kosong(x):
        return None, ""
    if isinstance(x, (int, float)):
        return None, str(x)
    t = pd.to_datetime(x, errors="coerce", dayfirst=True)
    if pd.isna(t):
        return None, str(x).strip()
    return t, t.strftime("%d/%m/%Y")


def baca_summary(xls):
    raw = xls.parse("Summary RKA", header=None)
    baris = None
    for i in range(len(raw)):
        if "Expenses" in raw.iloc[i].astype(str).values:
            baris = i
            break
    if baris is None:
        return None
    df = raw.iloc[baris + 1:, :].copy()
    df.columns = raw.iloc[baris].astype(str).values
    df = df.loc[:, ~df.columns.str.startswith("nan")]
    df = df[df["Expenses"].notna()]
    # berhenti di baris TOTAL; catatan di bawahnya tidak ikut dibaca
    total_idx = df.index[df["Expenses"].astype(str).str.strip().str.upper() == "TOTAL"]
    if len(total_idx):
        df = df.loc[: total_idx[0]].iloc[:-1]
    df = df[pd.to_numeric(df["Line"], errors="coerce").notna()]
    df["Realisasi Excel"] = pd.to_numeric(df["Realisasi (USD)"], errors="coerce")
    for k in ["Budget SKK (USD)", "Budget Internal (USD)"]:
        df[k] = pd.to_numeric(df[k], errors="coerce").fillna(0.0)
    return df[["Line", "Expenses", "Budget SKK (USD)", "Budget Internal (USD)", "Realisasi Excel"]].reset_index(drop=True)


def petakan_expense(judul, sheet, daftar):
    for e in daftar:
        if judul.strip().lower() == str(e).strip().lower():
            return e
    for e in daftar:
        if str(e).strip().lower() in sheet.lower():
            return e
    if "welfare" in sheet.lower():
        for e in daftar:
            if str(e).strip().lower() == "asuransi kesehatan":
                return e
    return None


def baca_detail(xls, daftar_expense):
    """Cari semua tabel pembayaran (yang punya kolom 'Docs No.') di semua sheet detail."""
    hasil, tak_terpetakan = [], set()
    for sheet in xls.sheet_names:
        if sheet.strip().lower() == "summary rka":
            continue
        g = xls.parse(sheet, header=None)
        n_r, n_c = g.shape
        for r in range(n_r - 1):
            for c in range(n_c):
                v = g.iat[r, c]
                if not (isinstance(v, str) and v.strip().lower().startswith("docs no")):
                    continue
                # kolom "No."
                no_col = None
                for cc in range(c - 1, max(c - 5, -1), -1):
                    t = g.iat[r, cc]
                    if isinstance(t, str) and t.strip().lower() in ("no.", "no"):
                        no_col = cc
                        break
                if no_col is None:
                    no_col = max(c - 2, 0)
                label_cols = list(range(no_col + 1, c))
                if not label_cols:
                    continue
                kepala = g.iat[r, label_cols[0]]
                tipe_bulan = isinstance(kepala, str) and kepala.strip().lower().startswith("month")
                # judul tabel (dicari ke atas)
                judul = ""
                for rr in range(r - 1, max(r - 11, -1), -1):
                    t = g.iat[rr, label_cols[0]]
                    if isinstance(t, str) and t.strip() and t.strip().lower() not in ABAIKAN:
                        judul = t.strip()
                        break
                expense = petakan_expense(judul, sheet, daftar_expense)
                if expense is None:
                    tak_terpetakan.add(f"{judul or '(tanpa judul)'} [{sheet}]")
                    expense = "Belum terpetakan"
                bulan_aktif, bulan_teks, no_aktif = None, "", ""
                for rr in range(r + 2, n_r):
                    no_val = g.iat[rr, no_col]
                    labels = [g.iat[rr, cc] for cc in label_cols]
                    if isinstance(no_val, str) and no_val.strip().lower() in ("no.", "no"):
                        break
                    if any(isinstance(t, str) and t.strip().lower() in ("total", "description")
                           for t in labels + [no_val]):
                        break
                    if tipe_bulan:
                        p = parse_bulan(labels[0])
                        if p is not None:
                            bulan_aktif, bulan_teks = p, str(labels[0]).strip()
                        item = str(labels[-1]).strip() if len(labels) > 1 and not kosong(labels[-1]) else ""
                    else:
                        item = " ".join(str(x).strip() for x in labels if not kosong(x))
                    if not kosong(no_val):
                        no_aktif = teks_dok(no_val)
                    docs = g.iat[rr, c]
                    nominal = angka(g.iat[rr, c + 1]) if c + 1 < n_c else 0.0
                    kurs = angka(g.iat[rr, c + 2]) if c + 2 < n_c else 0.0
                    tahap = [g.iat[rr, c + 4 + i] if c + 4 + i < n_c else None for i in range(5)]
                    if not (not kosong(docs) or nominal > 0 or any(not kosong(t) for t in tahap)):
                        continue
                    if kurs > 0:
                        nilai_usd = nominal / kurs
                    else:
                        nilai_usd = angka(g.iat[rr, c + 3]) if c + 3 < n_c else 0.0
                    tgl, teks = [], []
                    for t in tahap:
                        d, s = baca_tanggal(t)
                        tgl.append(d)
                        teks.append(s)
                    terakhir = "Belum diproses"
                    for i in range(4, -1, -1):
                        if teks[i]:
                            terakhir = TAHAP[i]
                            break
                    valid = [d for d in tgl if d is not None]
                    if tipe_bulan and bulan_aktif is not None:
                        periode = bulan_aktif
                    elif valid:
                        periode = min(valid).replace(day=1).normalize()
                    else:
                        periode = pd.NaT
                    if tipe_bulan and bulan_teks:
                        label_bulan = bulan_teks
                    elif valid:
                        label_bulan = BULAN_PENDEK[min(valid).month - 1] + " " + str(min(valid).year)
                    else:
                        label_bulan = "-"
                    baris = {"Expense": expense, "Kategori": judul, "No": no_aktif, "Bulan": label_bulan,
                             "Item": item, "No. Dokumen": teks_dok(docs), "IDR": nominal, "Kurs": kurs,
                             "USD": nilai_usd, "Periode": periode, "Status Terakhir": terakhir,
                             "Kurs kosong": nominal > 0 and kurs <= 0}
                    for i, nama in enumerate(TAHAP):
                        baris[nama] = teks[i]
                    hasil.append(baris)
    df = pd.DataFrame(hasil)
    if not df.empty:
        df["Periode"] = pd.to_datetime(df["Periode"])
    return df, sorted(tak_terpetakan)


def deteksi_perusahaan(nama_file, xls):
    """Tebak PEB atau PENN dari nama file, lalu dari teks di bagian atas sheet Summary RKA."""
    def cari(teks):
        t = str(teks).upper()
        if re.search(r"(?<![A-Z])PENN(?![A-Z])", t):
            return "PENN"
        if re.search(r"(?<![A-Z])PEB(?![A-Z])", t) or "BAWEAN" in t:
            return "PEB"
        return ""
    hasil = cari(os.path.basename(str(nama_file)))
    if hasil:
        return hasil
    try:
        atas = xls.parse("Summary RKA", header=None, nrows=6)
        for v in atas.values.flatten():
            if isinstance(v, str):
                hasil = cari(v)
                if hasil:
                    return hasil
    except Exception:
        pass
    return ""


@st.cache_data(show_spinner="Membaca Excel...")
def proses_excel(isi, nama):
    """Baca satu file Excel (hasilnya disimpan sementara supaya tidak dibaca ulang)."""
    xls = None
    try:
        xls = pd.ExcelFile(io.BytesIO(isi))
        tebakan = deteksi_perusahaan(nama, xls)
        data = baca_summary(xls)
        if data is None or data.empty:
            return {"error": "Tabel di sheet 'Summary RKA' tidak ditemukan.", "tebakan": tebakan}
        try:
            trx, tak = baca_detail(xls, data["Expenses"].tolist())
            peringatan = ""
        except Exception as e:
            trx, tak = pd.DataFrame(), []
            peringatan = f"Detail pembayaran belum bisa dibaca ({e}). Dashboard memakai angka dari sheet Summary RKA."
        return {"error": "", "data": data, "trx": trx, "tak": tak, "peringatan": peringatan, "tebakan": tebakan}
    except Exception as e:
        return {"error": f"Gagal membaca file. Pastikan ada sheet bernama 'Summary RKA'. Detail: {e}",
                "tebakan": deteksi_perusahaan(nama, xls)}


def fmt_angka(x, desimal=2):
    """Format Indonesia: titik untuk ribuan, koma untuk desimal."""
    s = f"{x:,.{desimal}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


@st.cache_data(ttl=3600, show_spinner="Mengambil kurs terbaru dari internet...")
def ambil_kurs(hari=45):
    """Ambil kurs USD ke IDR. Kalau gagal, error dilempar supaya tidak ikut tersimpan di cache."""
    akhir = date.today()
    awal = akhir - timedelta(days=hari)
    for base in ["https://api.frankfurter.dev/v1", "https://api.frankfurter.app"]:
        try:
            r = requests.get(f"{base}/{awal}..{akhir}", params={"base": "USD", "symbols": "IDR"}, timeout=10)
            r.raise_for_status()
            rates = r.json()["rates"]
            df = pd.DataFrame([{"Tanggal": pd.Timestamp(k), "Kurs": float(v["IDR"])} for k, v in rates.items()])
            if len(df):
                return {"df": df.sort_values("Tanggal").reset_index(drop=True),
                        "sumber": "Frankfurter (data bank sentral Eropa / ECB)"}
        except Exception:
            continue
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        r.raise_for_status()
        j = r.json()
        tgl = pd.to_datetime(j.get("time_last_update_utc"), errors="coerce")
        tgl = tgl.tz_localize(None).normalize() if pd.notna(tgl) else pd.Timestamp(date.today())
        return {"df": pd.DataFrame([{"Tanggal": tgl, "Kurs": float(j["rates"]["IDR"])}]),
                "sumber": "ExchangeRate-API (hanya kurs terbaru)"}
    except Exception as e:
        raise RuntimeError(f"Tidak bisa terhubung ke layanan kurs: {e}")


def tampilkan_kurs():
    st.divider()
    st.header("💱 Kurs IDR - USD")
    st.caption("Kurs referensi dari internet. Data disegarkan tiap jam, tetapi sumbernya memperbarui satu kali per hari kerja. "
               "Ini bukan kurs BI, kurs pajak, atau kurs bank, jadi untuk transaksi resmi tetap gunakan kurs yang ditetapkan perusahaan.")
    if st.button("🔄 Perbarui kurs sekarang", key="btn_kurs"):
        ambil_kurs.clear()
    try:
        hasil = ambil_kurs()
    except Exception as e:
        hasil = None
        st.warning(f"Kurs dari internet belum bisa diambil ({e}). Kalkulator tetap bisa dipakai dengan kurs manual.")

    terbaru = None
    if hasil is not None:
        df = hasil["df"].copy()
        terbaru = float(df["Kurs"].iloc[-1])
        tgl_terbaru = df["Tanggal"].iloc[-1].strftime("%d/%m/%Y")
        sebelumnya = float(df["Kurs"].iloc[-2]) if len(df) >= 2 else None
        tiga_puluh = df.tail(30)
        a1, a2, a3, a4 = st.columns(4)
        a1.metric(f"1 USD ({tgl_terbaru})", f"Rp {fmt_angka(terbaru)}",
                  f"{terbaru - sebelumnya:+,.2f}".replace(",", "") if sebelumnya else None, delta_color="off")
        if len(df) >= 2:
            a2.metric("Rata-rata 30 hari kerja", f"Rp {fmt_angka(tiga_puluh['Kurs'].mean())}")
            a3.metric("Tertinggi", f"Rp {fmt_angka(tiga_puluh['Kurs'].max())}")
            a4.metric("Terendah", f"Rp {fmt_angka(tiga_puluh['Kurs'].min())}")
        st.caption(f"Sumber: {hasil['sumber']}")

    # ---- kalkulator
    st.subheader("Kalkulator")
    k1, k2 = st.columns(2)
    with k1:
        arah = st.radio("Konversi", ["USD → IDR", "IDR → USD"], horizontal=True, key="kurs_arah")
        jumlah = st.number_input("Jumlah", min_value=0.0, value=1000.0 if arah == "USD → IDR" else 16_000_000.0,
                                 step=100.0, format="%.2f", key=f"kurs_jumlah_{arah}")
    with k2:
        pilihan_kurs = ["Kurs terbaru (internet)", "Kurs manual"] if terbaru else ["Kurs manual"]
        sumber_kurs = st.radio("Kurs yang dipakai", pilihan_kurs, horizontal=True, key="kurs_sumber")
        if sumber_kurs == "Kurs manual":
            kurs_pakai = st.number_input("Kurs IDR per 1 USD", min_value=1.0, value=float(round(terbaru)) if terbaru else 16000.0,
                                         step=50.0, format="%.2f", key="kurs_manual")
        else:
            kurs_pakai = terbaru
            st.write(f"Kurs dipakai: **Rp {fmt_angka(kurs_pakai)}** per 1 USD")
    if arah == "USD → IDR":
        st.success(f"USD {fmt_angka(jumlah)} = **Rp {fmt_angka(jumlah * kurs_pakai)}**")
    else:
        st.success(f"Rp {fmt_angka(jumlah)} = **USD {fmt_angka(jumlah / kurs_pakai)}**")

    # ---- tabel & grafik
    if hasil is not None and len(hasil["df"]) >= 2:
        st.subheader("Riwayat kurs (hari kerja terakhir)")
        d = hasil["df"].copy()
        d["Perubahan"] = d["Kurs"].diff()
        d["Persen"] = d["Kurs"].pct_change() * 100
        garis = alt.Chart(d).mark_line(color=BIRU, point=alt.OverlayMarkDef(color=BIRU, size=40)).encode(
            x=alt.X("Tanggal:T", title=None, axis=alt.Axis(format="%d %b")),
            y=alt.Y("Kurs:Q", title="Rp per 1 USD", scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("Tanggal:T", format="%d/%m/%Y"), alt.Tooltip("Kurs:Q", format=",.2f", title="Rp per USD")])
        st.altair_chart(gaya(garis, "Pergerakan kurs USD → IDR", 280), width="stretch")
        tabel = d.sort_values("Tanggal", ascending=False).copy()
        tabel["Tanggal"] = tabel["Tanggal"].dt.strftime("%d/%m/%Y")
        tabel["1 USD = (Rp)"] = tabel["Kurs"].apply(fmt_angka)
        tabel["Perubahan (Rp)"] = tabel["Perubahan"].apply(lambda x: "-" if pd.isna(x) else f"{x:+,.2f}".replace(",", ""))
        tabel["Perubahan (%)"] = tabel["Persen"].apply(lambda x: "-" if pd.isna(x) else f"{x:+.2f}%")
        st.dataframe(tabel[["Tanggal", "1 USD = (Rp)", "Perubahan (Rp)", "Perubahan (%)"]].head(30),
                     hide_index=True, width="stretch")


# =====================================================================
#  UPLOAD
# =====================================================================
kepala = st.container()
st.caption("Upload file Excel monitoring Anda. Data hanya dibaca sementara dan tidak disimpan di server.")


def tampilkan_kepala(pt):
    with kepala:
        kiri, kanan = st.columns([4, 1])
        with kiri:
            st.title("👋 Halo Philip" + (f" - {pt}" if pt else ""))
            st.subheader(f"HR {pt} 2027 · RKA Budget Tracker" if pt else "HR 2027 · RKA Budget Tracker")
        with kanan:
            st.markdown(
                f'<div style="display:flex;justify-content:flex-end"><div class="logo-box">'
                f'<img src="data:image/png;base64,{LOGO_B64}" alt="Prima Energy"></div></div>',
                unsafe_allow_html=True)


files = st.file_uploader("Upload file Excel PEB dan PENN (boleh dua sekaligus)", type=["xlsx"],
                         accept_multiple_files=True)
if not files:
    tampilkan_kepala("")
    st.info("Silakan upload file Excel dulu. Anda bisa upload Excel PEB dan PENN sekaligus.")
    tampilkan_kurs()
    st.stop()

hasil_file = [proses_excel(f.getvalue(), f.name) for f in files]
tebakan = [h["tebakan"] for h in hasil_file]
terdeteksi = [t for t in tebakan if t]
perlu_cek = ("" in tebakan) or len(set(terdeteksi)) < len(terdeteksi)

OPSI_PT = ["(pilih)", "PEB", "PENN"]
pilihan_file = []
with st.expander("📁 File yang diupload", expanded=perlu_cek):
    st.caption("Perusahaan dibaca otomatis dari nama file atau isi Excel. Ubah di sini kalau salah.")
    for i, (f, h) in enumerate(zip(files, hasil_file)):
        c_nama, c_pt = st.columns([3, 1])
        c_nama.write(f"📄 {f.name}" + (" ⚠️ gagal dibaca" if h["error"] else ""))
        pilihan_file.append(c_pt.selectbox("Perusahaan", OPSI_PT, index=OPSI_PT.index(tebakan[i]) if tebakan[i] in OPSI_PT else 0,
                                           key=f"pt_{i}_{f.name}", label_visibility="collapsed"))

penetapan, duplikat = {}, set()
for i, pt in enumerate(pilihan_file):
    if pt == "(pilih)":
        continue
    if pt in penetapan:
        duplikat.add(pt)
        continue
    penetapan[pt] = i
if duplikat:
    st.warning("Ada lebih dari satu file untuk " + ", ".join(sorted(duplikat)) +
               ". Hanya file pertama yang dipakai. Ubah pilihan di bagian 'File yang diupload'.")
if not penetapan:
    tampilkan_kepala("")
    st.info("Nama perusahaan belum terdeteksi. Buka 'File yang diupload' lalu pilih PEB atau PENN untuk tiap file.")
    tampilkan_kurs()
    st.stop()

tersedia = [p for p in ["PEB", "PENN"] if p in penetapan]
if len(tersedia) > 1:
    PERUSAHAAN = st.radio("Pilih perusahaan", tersedia, horizontal=True, key="pilih_pt")
else:
    PERUSAHAAN = tersedia[0]

tampilkan_kepala(PERUSAHAAN)
h = hasil_file[penetapan[PERUSAHAAN]]
if h["error"]:
    st.error(h["error"])
    tampilkan_kurs()
    st.stop()

data, trx, tak_terpetakan = h["data"], h["trx"], h["tak"]
if h["peringatan"]:
    st.warning(h["peringatan"])
if tak_terpetakan:
    st.warning("Tabel berikut belum cocok dengan nama di Summary RKA: " + "; ".join(tak_terpetakan))

# =====================================================================
#  PERHITUNGAN
# =====================================================================
basis = st.radio("Basis budget", ["SKK", "Internal"], horizontal=True)
kolom_budget = "Budget SKK (USD)" if basis == "SKK" else "Budget Internal (USD)"
data["Budget"] = data[kolom_budget]

if trx.empty:
    data["Realisasi"] = data["Realisasi Excel"].fillna(0.0)
else:
    data["Realisasi"] = data["Expenses"].map(trx.groupby("Expense")["USD"].sum()).fillna(0.0)

if data["Budget"].sum() == 0:
    st.warning(f"Budget {basis} di sheet Summary masih 0 semua, jadi persentase tidak bisa dihitung.")

data["Total Terpakai"] = data["Realisasi"]
data["Sisa"] = data["Budget"] - data["Total Terpakai"]
data["Persen"] = (data["Total Terpakai"] / data["Budget"]).where(data["Budget"] > 0, 0.0)
# Realisasi dibebankan ke basis yang dipilih; budget lainnya ditampilkan utuh
if basis == "SKK":
    data["Sisa SKK"] = data["Budget SKK (USD)"] - data["Total Terpakai"]
    data["Sisa Internal"] = data["Budget Internal (USD)"]
else:
    data["Sisa SKK"] = data["Budget SKK (USD)"]
    data["Sisa Internal"] = data["Budget Internal (USD)"] - data["Total Terpakai"]

urutan = data["Expenses"].tolist()

# =====================================================================
#  BAGIAN ATAS: ANGKA BUDGET
# =====================================================================
total_budget = data["Budget"].sum()
total_pakai = data["Total Terpakai"].sum()
total_sisa = total_budget - total_pakai
persen_total = total_pakai / total_budget if total_budget > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Budget", usd(total_budget))
c2.metric("Terpakai", usd(total_pakai))
c3.metric("Sisa", usd(total_sisa))
c4.metric("Utilisasi", f"{persen_total:.1%}")
st.progress(min(max(persen_total, 0.0), 1.0))

st.divider()

# =====================================================================
#  BAGIAN TENGAH: GRAFIK
# =====================================================================
st.header("📊 Grafik Budget")


def kartu(r):
    p = r["Persen"]
    warna = MERAH if p >= 1 else (KUNING if p >= 0.8 else HIJAU)
    lebar = min(max(p, 0), 1) * 100
    pct_txt = f"{p:.0%} terpakai" if r["Budget"] > 0 else "budget belum diisi"

    def baris_sisa(nama, budget, sisa):
        if budget <= 0 and sisa == 0:
            return f'<div class="fm-row"><span>{nama}</span><b class="mut">belum ada budget</b></div>'
        kelas = "neg" if sisa < 0 else "pos"
        return f'<div class="fm-row"><span>{nama}</span><b class="{kelas}">{usd(sisa)}</b></div>'

    return (f'<div class="fm-card"><div class="fm-top"><span class="fm-name">{html.escape(str(r["Expenses"]))}</span>'
            f'<span class="fm-line">Line {html.escape(str(r["Line"]))}</span></div>'
            f'<div class="fm-bar"><div class="fm-fill" style="width:{lebar:.0f}%;background:{warna}"></div></div>'
            f'<div class="fm-pct">{pct_txt}</div>'
            f'<div class="fm-row"><span>Terpakai</span><b>{usd(r["Total Terpakai"])}</b></div>'
            f'{baris_sisa("Sisa SKK", r["Budget SKK (USD)"], r["Sisa SKK"])}'
            f'{baris_sisa("Sisa Internal", r["Budget Internal (USD)"], r["Sisa Internal"])}</div>')


kolom_kartu = st.columns(4)
for i, (_, r) in enumerate(data.iterrows()):
    with kolom_kartu[i % 4]:
        st.markdown(kartu(r), unsafe_allow_html=True)
st.caption(f"Realisasi dibebankan ke budget {basis} (sesuai pilihan basis di atas). Budget lainnya ditampilkan utuh.")

# --- tahun & deret bulanan keseluruhan
if not trx.empty and trx["Periode"].notna().any():
    tahun = int(trx["Periode"].dropna().dt.year.mode().iloc[0])
else:
    tahun = 2027


def deret_bulanan(df):
    b = pd.DataFrame({"Periode": [pd.Timestamp(tahun, m, 1) for m in range(1, 13)], "Bulan": BULAN_PENDEK})
    if df is not None and not df.empty:
        g = df.dropna(subset=["Periode"]).groupby("Periode")["USD"].sum()
        b["Pengeluaran"] = b["Periode"].map(g).fillna(0.0)
    else:
        b["Pengeluaran"] = 0.0
    return b


g1, g2 = st.columns(2)

with g1:
    ov = data[["Expenses", "Budget", "Total Terpakai", "Sisa", "Persen"]].copy()
    panjang = pd.concat([
        pd.DataFrame({"Expenses": ov["Expenses"], "Jenis": "Terpakai", "Nilai": ov["Total Terpakai"], "Urut": 0}),
        pd.DataFrame({"Expenses": ov["Expenses"], "Jenis": "Sisa", "Nilai": ov["Sisa"].clip(lower=0), "Urut": 1}),
    ])
    batang = alt.Chart(panjang).mark_bar().encode(
        y=alt.Y("Expenses:N", sort=urutan, title=None),
        x=alt.X("Nilai:Q", stack="zero", title="USD"),
        color=alt.Color("Jenis:N", scale=alt.Scale(domain=["Terpakai", "Sisa"], range=[KUNING, BIRU]),
                        legend=alt.Legend(title=None)),
        order=alt.Order("Urut:Q"),
        tooltip=[alt.Tooltip("Expenses:N"), alt.Tooltip("Jenis:N"), alt.Tooltip("Nilai:Q", format=",.0f")])
    ov["Ujung"] = ov[["Budget", "Total Terpakai"]].max(axis=1)
    ov["Label"] = ov.apply(lambda r: f"{r['Persen']:.0%}" if r["Budget"] > 0 else "-", axis=1)
    teks = alt.Chart(ov).mark_text(align="left", dx=5, color=TXT).encode(
        y=alt.Y("Expenses:N", sort=urutan), x="Ujung:Q", text="Label:N")
    st.altair_chart(gaya(batang + teks, f"Budget {basis}: terpakai vs sisa per kategori", 340), width="stretch")

with g2:
    bln_all = deret_bulanan(trx)
    aktif = bln_all[bln_all["Pengeluaran"] > 0]
    if total_budget > 0 and not aktif.empty:
        terakhir = aktif.index.max()
        sisa_list = [("Awal", total_budget)]
        kum = 0.0
        for idx in range(terakhir + 1):
            kum += bln_all.loc[idx, "Pengeluaran"]
            sisa_list.append((bln_all.loc[idx, "Bulan"], total_budget - kum))
        d_sisa = pd.DataFrame(sisa_list, columns=["Label", "Sisa"])
        urut_x = ["Awal"] + BULAN_PENDEK
        dasar = alt.Chart(d_sisa).encode(
            x=alt.X("Label:N", sort=urut_x, title=None, axis=alt.Axis(labelAngle=0),
                    scale=alt.Scale(domain=urut_x)),
            y=alt.Y("Sisa:Q", title="USD", scale=alt.Scale(domain=[0, total_budget * 1.03])),
            tooltip=[alt.Tooltip("Label:N", title="Akhir bulan"), alt.Tooltip("Sisa:Q", title="Sisa budget", format=",.0f")])
        area = dasar.mark_area(color=HIJAU, opacity=0.25, line={"color": HIJAU})
        titik = dasar.mark_point(color=HIJAU, filled=True, size=70)
        st.altair_chart(gaya(area + titik, f"Pergerakan sisa budget {basis} per bulan (semua kategori)", 340), width="stretch")
    else:
        st.info("Grafik pergerakan sisa budget akan muncul setelah ada pembayaran yang punya tanggal atau bulan di Excel.")

if not trx.empty:
    tanpa_bulan = int(trx["Periode"].isna().sum())
    if tanpa_bulan:
        st.caption(f"⚠️ {tanpa_bulan} pembayaran belum punya bulan/tanggal proses, jadi belum masuk grafik bulanan "
                   "(isi tanggal PR Submit di Excel).")

st.divider()

# =====================================================================
#  BAGIAN BAWAH: DETAIL PER KATEGORI
# =====================================================================
st.header("📋 Detail per Kategori")


def no_line(x):
    try:
        return str(int(float(x)))
    except (TypeError, ValueError):
        return str(x)


pilihan = [f"{no_line(r['Line'])} - {r['Expenses']}" for _, r in data.iterrows()]
pilih = st.selectbox("Pilih kategori", pilihan, key=f"kategori_{PERUSAHAAN}")
r = data.iloc[pilihan.index(pilih)]
nama = r["Expenses"]

t = trx[trx["Expense"] == nama].copy() if not trx.empty else pd.DataFrame()
sudah_paid = t.loc[t["Paid"] != "", "USD"].sum() if not t.empty else 0.0


def nilai_budget(x):
    return usd(x) if x > 0 else "Belum diisi"


st.markdown(f"### {pilih}")
d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Budget SKK", nilai_budget(r["Budget SKK (USD)"]))
d2.metric("Budget Internal", nilai_budget(r["Budget Internal (USD)"]))
d3.metric("Sudah keluar", usd(r["Total Terpakai"]))
d4.metric("Sisa SKK", usd(r["Sisa SKK"]))
d5.metric("Sisa Internal", usd(r["Sisa Internal"]) if (r["Budget Internal (USD)"] > 0 or r["Sisa Internal"] != 0) else "Belum diisi")
if r["Budget"] > 0:
    st.progress(min(max(r["Persen"], 0.0), 1.0))
    st.caption(f"{r['Persen']:.1%} dari budget {basis} sudah terpakai. "
               f"Dari total yang keluar, {usd(sudah_paid)} sudah berstatus Paid.")

if t.empty:
    st.info("Belum ada pembayaran yang terisi untuk kategori ini di Excel.")
else:
    bln = deret_bulanan(t)
    aktif_k = bln[bln["Pengeluaran"] > 0]
    rata = aktif_k["Pengeluaran"].mean() if len(aktif_k) else 0.0
    jatah = r["Budget"] / 12 if r["Budget"] > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Total ({len(t)} pembayaran)", usd(t["USD"].sum()))
    m2.metric("Rata-rata per bulan", usd(rata) if len(aktif_k) else "-")
    if len(aktif_k):
        puncak = aktif_k.loc[aktif_k["Pengeluaran"].idxmax()]
        m3.metric("Bulan tertinggi", f"{puncak['Bulan']} ({usd(puncak['Pengeluaran'])})")
    else:
        m3.metric("Bulan tertinggi", "-")
    if len(aktif_k) >= 2:
        selisih = aktif_k["Pengeluaran"].iloc[-1] - aktif_k["Pengeluaran"].iloc[-2]
        arah = "naik" if selisih > 0 else ("turun" if selisih < 0 else "stabil")
        m4.metric(f"Tren ({aktif_k['Bulan'].iloc[-1]} vs {aktif_k['Bulan'].iloc[-2]})",
                  arah.capitalize(), f"{selisih:+,.0f} USD", delta_color="inverse")
    else:
        m4.metric("Tren", "-", help="Butuh minimal 2 bulan yang ada pengeluaran")

    if len(aktif_k):
        k1, k2 = st.columns(2)
        with k1:
            bar = alt.Chart(bln).mark_bar(color=BIRU, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X("Bulan:N", sort=BULAN_PENDEK, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Pengeluaran:Q", title="USD"),
                tooltip=[alt.Tooltip("Bulan:N"), alt.Tooltip("Pengeluaran:Q", format=",.0f")])
            nama_rata, nama_jatah = "Rata-rata per bulan", "Jatah per bulan (budget ÷ 12)"
            garis_df = pd.DataFrame({"Garis": [nama_rata, nama_jatah], "Nilai": [rata, jatah]})
            garis_df = garis_df[garis_df["Nilai"] > 0]
            garis = alt.Chart(garis_df).mark_rule(strokeWidth=2).encode(
                y="Nilai:Q",
                color=alt.Color("Garis:N", scale=alt.Scale(domain=[nama_rata, nama_jatah], range=[KUNING, HIJAU]),
                                legend=alt.Legend(title=None)),
                strokeDash=alt.StrokeDash("Garis:N", scale=alt.Scale(domain=[nama_rata, nama_jatah],
                                                                     range=[[1, 0], [6, 4]]), legend=None))
            st.altair_chart(gaya(bar + garis, f"{nama}: pengeluaran per bulan", 300), width="stretch")
        with k2:
            bln["Kumulatif"] = bln["Pengeluaran"].cumsum()
            sampai = bln[bln["Pengeluaran"] > 0].index.max()
            kum_df = bln.loc[:sampai]
            batas = max(r["Budget"], kum_df["Kumulatif"].max()) * 1.05
            garis_kum = alt.Chart(kum_df).mark_line(color=KUNING, point=alt.OverlayMarkDef(color=KUNING, size=70)).encode(
                x=alt.X("Bulan:N", sort=BULAN_PENDEK, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Kumulatif:Q", title="USD", scale=alt.Scale(domain=[0, batas])),
                tooltip=[alt.Tooltip("Bulan:N"), alt.Tooltip("Kumulatif:Q", format=",.0f", title="Total terpakai")])
            lapis = garis_kum
            if r["Budget"] > 0:
                batas_budget = alt.Chart(pd.DataFrame({"y": [r["Budget"]]})).mark_rule(
                    color=MERAH, strokeDash=[6, 4], strokeWidth=2).encode(y="y:Q")
                lapis = garis_kum + batas_budget
            st.altair_chart(gaya(lapis, f"{nama}: progres pengeluaran (garis merah = budget {basis})", 300),
                            width="stretch")
    else:
        st.info("Grafik bulanan akan muncul setelah pembayaran punya bulan atau tanggal proses (mis. tanggal PR Submit).")

    # --- rincian pembayaran (kartu siap presentasi)
    st.markdown("#### Rincian setiap pembayaran")
    banyak_sub = t["Kategori"].nunique() > 1

    def kartu_bayar(b):
        bagian = []
        if banyak_sub and b["Kategori"]:
            bagian.append(b["Kategori"])
        if b["Item"]:
            bagian.append(b["Item"])
        if b["Bulan"] and b["Bulan"] != "-":
            bagian.append(b["Bulan"])
        judul = " • ".join(bagian) if bagian else "Pembayaran"
        no = f"#{b['No']} " if b["No"] else ""
        dok = f"No. Dokumen: <b>{html.escape(b['No. Dokumen'])}</b>" if b["No. Dokumen"] else "No. Dokumen: belum diisi"
        kurs_txt = f" @ {b['Kurs']:,.0f}".replace(",", ".") if b["Kurs"] > 0 else " (kurs belum diisi)"
        chips = ""
        for nama_tahap in TAHAP:
            isi = b[nama_tahap]
            if isi:
                chips += f'<div class="chip on">{nama_tahap}<small>{html.escape(isi)}</small></div>'
            else:
                chips += f'<div class="chip off">{nama_tahap}<small>-</small></div>'
        status = b["Status Terakhir"]
        badge = "✅ Paid" if status == "Paid" else status
        return (f'<div class="pay-card"><div class="pay-head"><span class="pay-title">{no}{html.escape(judul)}</span>'
                f'<span class="pay-badge">{html.escape(badge)}</span></div>'
                f'<div class="pay-doc">{dok}</div>'
                f'<div class="pay-amt">{idr(b["IDR"])}{kurs_txt} = <b>USD {b["USD"]:,.2f}</b></div>'
                f'<div class="chips">{chips}</div></div>')

    kolom_bayar = st.columns(2)
    for i, (_, b) in enumerate(t.iterrows()):
        with kolom_bayar[i % 2]:
            st.markdown(kartu_bayar(b), unsafe_allow_html=True)
    st.caption(f"Total: {idr(t['IDR'].sum())}  •  {usd(t['USD'].sum())}  •  {len(t)} pembayaran")
    if t["Kurs kosong"].any():
        st.warning(f"{int(t['Kurs kosong'].sum())} pembayaran punya nominal IDR tetapi Kurs masih kosong, "
                   "sehingga nilai USD-nya dihitung 0.")

    with st.expander("Lihat sebagai tabel"):
        tampil = t.copy()
        tampil["IDR"] = tampil["IDR"].apply(idr)
        tampil["Kurs"] = tampil["Kurs"].apply(lambda x: f"{x:,.0f}".replace(",", ".") if x > 0 else "-")
        tampil["USD"] = tampil["USD"].apply(lambda x: f"{x:,.2f}")
        kolom_tampil = ["No", "Kategori", "Bulan", "Item", "No. Dokumen", "IDR", "Kurs", "USD"] + TAHAP + ["Status Terakhir"]
        if not banyak_sub:
            kolom_tampil.remove("Kategori")
        if (tampil["Item"] == "").all():
            kolom_tampil.remove("Item")
        st.dataframe(tampil[kolom_tampil], hide_index=True, width="stretch")

# =====================================================================
#  CEK KONSISTENSI
# =====================================================================
st.divider()
with st.expander("🔎 Cek konsistensi dengan sheet Summary RKA"):
    cek = data[["Expenses", "Realisasi Excel", "Realisasi"]].copy()

    def catatan(r):
        if pd.isna(r["Realisasi Excel"]):
            return "Summary Excel error (#DIV/0!). Dashboard menghitung sendiri dari rincian."
        if abs(r["Realisasi Excel"] - r["Realisasi"]) > 1:
            return "Ada selisih, mohon dicek."
        return "Sama"

    cek["Catatan"] = cek.apply(catatan, axis=1)
    cek = cek.rename(columns={"Realisasi Excel": "Realisasi di Summary (USD)", "Realisasi": "Realisasi di Dashboard (USD)"})
    st.dataframe(cek, hide_index=True, width="stretch")

tampilkan_kurs()
