#!/usr/bin/python
# -*- coding: utf-8 -*-
#   moldynplot.TimeSeriesFigureManager.py
#
#   Copyright (C) 2015 Karl T Debiec
#   All rights reserved.
#
#   This software may be modified and distributed under the terms of the
#   BSD license. See the LICENSE file for details.
"""
Generates one or more time series figures to specifications in a YAML
file.
"""
################################### MODULES ###################################
from __future__ import absolute_import,division,print_function,unicode_literals
if __name__ == "__main__":
    __package__ = str("moldynplot")
    import moldynplot
from .myplotspec.FigureManager import FigureManager
################################### CLASSES ###################################
class TimeSeriesFigureManager(FigureManager):
    """
    Manages the generation of time series figures
    """

    from .myplotspec.manage_defaults_presets import manage_defaults_presets
    from .myplotspec.manage_kwargs import manage_kwargs
    from .myplotspec.manage_output import manage_output

    defaults = """
        draw_subplot:
          xlabel: Time (ns)
          ylabel: RMSD (Å)
    """

    available_presets = """
      rmsd:
        class: content
        help: Root Mean Standard Deviation (RMSD) vs. time
        draw_subplot:
          ylabel: RMSD (Å)
        draw_dataset:
          dataset_kw:
            read_csv_kw:
              delim_whitespace: True
              index_col: False
              names: [time, rmsd]
              header: 0
      notebook:
        class: target
        inherits: notebook
        draw_figure:
          left:       0.50
          sub_width:  4.40
          right:      0.20
          bottom:     0.90
          sub_height: 1.80
          top:        0.40
          shared_legend: True
          shared_legend_kw:
            left:       0.50
            sub_width:  4.40
            right:      0.20
            bottom:     0.00
            sub_height: 0.50
            legend_kw:
              frameon: False
              labelspacing: 0.5
              legend_fp: 8r
              loc: 9
              ncol: 2
        draw_dataset:
          plot_kw:
            lw: 1.0
          partner_kw:
            position: right
            sub_width: 0.8
            title_fp: 10b
            label_fp: 10b
            tick_fp:   8r
            tick_params:
              length: 2
              pad: 6
      pdist:
        class: appearance
        help: Draw colorbar to right of plot
        draw_dataset:
          pdist: True
          partner_kw:
            position: right
            sub_width: 0.8
            xlabel:      Probability
            xticks:      [0.00,0.05,0.10]
            xticklabels: ["0.00","0.05","0.10"]
            yticks:      [0,1,2,3,4,5,6]
            yticklabels: []
    """

    @manage_defaults_presets()
    @manage_kwargs()
    def draw_dataset(self, subplot, dt=None, downsample=None, label="",
        handles=None, pdist=False, verbose=1, debug=0, **kwargs):
        from .myplotspec import get_color, multi_get_copy
        from .myplotspec.Dataset import Dataset
        import pandas as pd
        import numpy as np
        from os.path import expandvars

        # Load data
        dataset_kw = multi_get_copy("dataset_kw", kwargs, {})
        if "infile" in kwargs:
            dataset_kw["infile"] = kwargs["infile"]
        dataframe= self.load_dataset(Dataset, verbose=verbose, debug=debug,
          **dataset_kw).data

        # Scale:
        if dt is not None:
            dataframe["time"] *= dt

        # Downsample
        if downsample is not None:
            full_size = dataframe.shape[0]
            reduced_size = int(full_size / downsample)
            reduced = pd.DataFrame(0.0, index=range(0, reduced_size),
              columns=dataframe.columns, dtype=np.int64)
            for i in range(0, reduced_size):
                reduced.loc[i] = dataframe[
                  i*downsample:(i+1)*downsample+1].mean()
            dataframe = reduced

        # Configure plot settings
        plot_kw = multi_get_copy("plot_kw", kwargs, {})
        if "color" in plot_kw:
            plot_kw["color"] = get_color(plot_kw["color"])
        elif "color" in kwargs:
            plot_kw["color"] = get_color(kwargs.pop("color"))

        # Plot
        handle = subplot.plot(dataframe["time"], dataframe["rmsd"],
          **plot_kw)[0]
        if handles is not None:
            handles[label] = handle
        if pdist:
            from sklearn.neighbors import KernelDensity

            if not hasattr(subplot, "_mps_partner_subplot"):
                from .myplotspec.axes import add_partner_subplot
                add_partner_subplot(subplot, **kwargs)
            kde_kw = multi_get_copy("kde_kw", kwargs, {"bandwidth": 0.1})
            grid = kwargs.get("grid", np.linspace(0,6,100))
            kde = KernelDensity(**kde_kw)
            kde.fit(dataframe["rmsd"][:, np.newaxis])
            pdf = np.exp(kde.score_samples(grid[:, np.newaxis]))
            pdf /= pdf.sum()
            pdist_kw = plot_kw.copy()
            pdist_kw.update(kwargs.get("pdist_kw", {}))
            subplot._mps_partner_subplot.plot(pdf, grid, **pdist_kw)

#################################### MAIN #####################################
if __name__ == "__main__":
    TimeSeriesFigureManager().main()
