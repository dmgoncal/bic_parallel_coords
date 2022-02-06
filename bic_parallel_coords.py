###############################################################################
### Author: Daniel Gonçalves                                                ###
### Email:  dmateusgoncalves@tecnico.ulisboa.pt                             ###
### Description:                                                            ###
###       - Bicluster parallel coordinates plot generator class             ###
###       - Works either with categorical XOR numerical data                ### 
###       - Requires input of original data file                            ###
###       - Requires input of "result.txt" file generated by BicPAMS        ###
###############################################################################

import plotly.express as px
import pandas as pd
import os

class BiclusterVisualizer:
    """
    The class containing all methods for bicluster loading and visualization

    ...

    Attributes
    ----------
    data_filename : str
        The name of the file containing the data
    bic_filename : str
        The name of the file containing the biclusters

    Methods
    -------
    load_data_arff(filename)
        Loads the data from an arff file
    load_data_csv(filename)
        Loads the data from a csv file
    load_data(filename)
        Chooses the approapriate method for loading data based on the file extension.
    load_biclusters(file)
        Loads the biclusters from a file
    plot_parallel_categories()
        Plots the parallel coordinates of the biclusters (suitable for numeric data)
    plot_parallel_categories()
        Plots the parallel categories of the biclusters (suitable for categorical data)
    """

    def __init__(self):
        """Constructor for the class"""
        self.counter = 0
        self.df = None
        self.outcome = None
        self.bic = None
        self.main_var = None

    def __load_data_arff(self,data_filename,line_labels=False):
        """Loads the data from an arff file

        Parameters
        ----------
        data_filename : str
            The name of the file containing the data

        Returns
        -------
        df : pandas.DataFrame
            DataFrame containing the dataset
        main_var : list
            List of dictionaries with information for each variable (name,values)
        """
        final_data = []
        final_cols = []
        main_var = []
        f = open(data_filename, "r")
        flag = 0
        data = []
        cols = []
        counter = 0
        for line in f:
            if line.strip():
                if flag==1:
                    data.append([i for i in line.rstrip("\n").split(",")])
                elif line.startswith("@ATTRIBUTE"):
                    counter+=1
                    if (counter>1) and len(line.split("{")[0])>1:
                        main_var.append(
                            {'var': ''.join(line.split("\t")[1].strip("[ ,'}\"\n]")),
                            'vals': [x.strip("[ ,'}\"\n]") for x in line.split("\t")[2].split(",")]})
                    else:
                        main_var.append(
                            {'var': ''.join(line.split("\t")[1].strip("[ ,'}\"\n]")),
                            'vals': []})
                    cols.append(line.split("\t")[1].strip())
                elif line.startswith("@DATA"):
                    flag=1
        for col in range(len(cols)):
            if cols[col] not in final_cols:
                final_cols.append(cols[col])
                for l in range(len(data)):
                    if len(final_data)>=l+1:
                        final_data[l].append(data[l][col])
                    else:
                        final_data.append([])
                        final_data[l].append(data[l][col])

        df = pd.DataFrame(data=final_data,columns=final_cols)
        df.dropna(how='all',inplace=True)
        return df, main_var

    def __load_data_csv(self,data_filename):
        """Loads the data from a csv file

        Parameters
        ----------
        data_filename : str
            The name of the file containing the data

        Returns
        -------
        df : pandas.DataFrame
            DataFrame containing the dataset
        main_var : list
            empty list (for compatibility with arff files)
        """
        f = open(data_filename, "r")
        data = []
        cols = None
        counter = 0
        for line in f:
            if counter==0:
                cols=[i for i in line.rstrip("\n").split(",")]
            else:
                data.append([i for i in line.rstrip("\n").split(",")])
            counter+=1
        df = pd.DataFrame(data,columns=cols)
        df.dropna(how='all',inplace=True)
        return df, []

    def __load_data_txt(self,data_filename):
        """Loads the data from a txt file

        Parameters
        ----------
        data_filename : str
            The name of the file containing the data

        Returns
        -------
        df : pandas.DataFrame
            DataFrame containing the dataset
        main_var : list
            empty list (for compatibility with arff files)
        """
        f = open(data_filename, "r")
        data = []
        cols = []
        counter = 0
        for line in f:
            if counter==1:
                cols=["lines"]
                cols.extend([i for i in line.split(": [")[1].rstrip("]\n").split(", ")])
            elif counter>1:
                data.append([i for i in line.rstrip("|\n").split("|")])
            counter+=1
        df = pd.DataFrame(data,columns=cols)
        df.dropna(how='all',inplace=True)
        return df, []
    
    def load_data(self,data_filename):
        """Chooses the approapriate method for loading data based on the file extension.
        
        (Can be overriden by the user to suit specific file formats)

        Parameters
        ----------
        data_filename : str
            The name of the file containing the data
        """
        if data_filename.endswith(".arff"):
            return self.__load_data_arff(data_filename)
        elif data_filename.endswith(".csv"):
            return self.__load_data_csv(data_filename)
        elif data_filename.endswith(".txt"):
            return self.__load_data_txt(data_filename)

    def load_biclusters(self,bic_filename):
        """Loads the biclusters from a results file and stores data in a dictionary.
        
        (Can be overriden by the user to suit specific file formats)

        Parameters
        ----------
        bic_filename : str
            The name of the file containing the biclusters

        Returns
        -------
        bic : dict
            Dictionary containing the biclusters.
        """
        f = open(bic_filename, "r")
        results = {}
        i = -1
        flag = 0
        bic_batch = []
        for line in f:  
            if line.strip():
                if line.startswith("FOUND"):
                    i+=1
                    bic_batch = []
                    flag = 1  
                elif line.startswith(" ") and flag==1:
                    current_bic = {}
                    for elem in line.split(" "):
                        if elem.startswith("I="):
                            pattern = elem.split("=")[1]
                            current_bic['pattern'] = pattern.lstrip("[").rstrip("]").split(',')
                        elif elem.startswith("Y="):
                            cols = elem.split("=")[1]  
                            current_bic['cols'] = cols.lstrip("[").rstrip("]").split(',')      
                        elif elem.startswith("X="):
                            lines = elem.split("=")[1]
                            current_bic['lines'] = [i for i in lines.lstrip("[").rstrip("]").split(',')]
                        elif elem.startswith("pvalue="):
                            pvalue = float(elem.split("=")[1])
                            current_bic['pvalue'] = pvalue
                        elif elem.startswith("Lifts="):
                            lifts = line.split("Lifts=")[1]
                            current_bic['lifts'] = [float(i) for i in lifts.lstrip("[").rstrip("]\n").split(',')]
                            break  
                    bic_batch.append(current_bic)
            else:
                if i>=0:
                    results[i] = bic_batch
                flag=0
        return results

    def plot_parallel_categories(self,bic,df,main_var,folder_name):
        """Plots the parallel categories of the biclusters (suitable for categorical data)

        Parameters
        ----------
        bic : dict
            Dictionary containing the bicluster's information.
        df : pandas.DataFrame
            DataFrame containing the dataset
        main_var : list
            List containing the main variables of the dataset.
        """
        if main_var:
            main_var = main_var[0]
        if len(set(df.iloc[:,0].values)) < len(df.iloc[:,0])/2:
            color = [1 if str(x) in bic['lines'] else 0 for x in range(len(df))]
        else:
            color = [1 if x in bic['lines'] else 0 for x in list(df.iloc[:,0].values)]
        df = df[bic['cols']]
        df.insert(len(df.columns), "color", color, True)
        fig = px.parallel_categories(
            data_frame=df, 
            color='color',
            color_continuous_scale='mint',
            dimensions = bic['cols'])
        if 'pvalue' in bic:
            lift = ''
            if (main_var and main_var['vals'] and "lifts" in bic):
                lift = "<br>Lift:<br>"
                for i in range(len(main_var['vals'])):
                    lift+="    "+main_var['vals'][i]+" = "+str(round(float(bic["lifts"][i]),3))+"<br>"
            fig.add_annotation(
                text="P-value = {:.3e}".format(bic['pvalue'])+lift,
                font_size=20,
                showarrow=False,
                align='left',
                yanchor='bottom',
                xanchor='right',
                yref="paper",
                xref='paper',
                y= -0.11,x = 1.1)
        fig.update_layout(
            margin = dict(l=125),
            coloraxis_colorbar=dict(
            title="In Bic",
            tickmode='array',
            tickvals = [0,1],
            ticktext = ['No','Yes'],
            x=1.1),
            font=dict(size=25))
        fig.update_traces(dimensions=[{"categoryorder":"category descending"} for x in range(len(bic['cols']))], selector=dict(type='parcats'))
        os.makedirs("results/ParallelCategories ("+folder_name+")/", exist_ok=True)
        fig.write_html("results/ParallelCategories ("+folder_name+")/pc_"+str(self.counter)+".html")
        self.counter += 1

    def plot_parallel_coordinates(self,bic,df,main_var,folder_name):
        """Plots the parallel coordinates of the biclusters (suitable for continuous data)

        Parameters
        ----------
        bic : dict
            Dictionary containing the bicluster's information.
        df : pandas.DataFrame
            DataFrame containing the dataset
        main_var : list
            List containing the main variables of the dataset.
        """
        if main_var:
            main_var = main_var[0]
        if len(set(df.iloc[:,0].values)) < len(df.iloc[:,0]):
            color = [1 if str(x) in bic['lines'] else 0 for x in range(len(df))]
        else:
            color = [1 if x in bic['lines'] else 0 for x in list(df.iloc[:,0].values)]
        df = df[bic['cols']]
        df.insert(len(df.columns), "color", color, True)
        df=df.replace(to_replace='?', value=float('nan'))
        df = df.apply(pd.to_numeric)
        fig = px.parallel_coordinates(
            df,
            color='color',
            color_continuous_scale='mint',
            dimensions = bic['cols'])
        if 'pvalue' in bic:
            lift = ''
            if main_var['vals'] and "lifts" in bic:
                lift = "<br>Lift:<br>"
                for i in range(len(main_var['vals'])):
                    lift+="    "+main_var['vals'][i]+" = "+str(round(float(bic["lifts"][i]),3))+"<br>"
            fig.add_annotation(
                text="P-value = {:.3e}".format(bic['pvalue'])+lift,
                showarrow=False,
                align='left',
                yanchor='bottom',
                xanchor='right',
                yref="paper",
                xref='paper',
                y= -0.1,x = 1.1)
        fig.update_layout(
            margin = dict(l=125),
            coloraxis_colorbar=dict(
            title="In Bic",
            tickmode='array',
            tickvals = [0,1],
            ticktext = ['No','Yes'],
            x=1.1),
            font=dict(size=25))
        os.makedirs("results/ParallelCoordinates ("+folder_name+")/", exist_ok=True)
        fig.write_html("results/ParallelCoordinates ("+folder_name+")/pc_"+str(self.counter)+".html")
        self.counter += 1

    def plot_bicluster(self,bic,df,main_var,folder_name,mode='categories'):
        """Chooses the approapriate method for plotting the biclusters.

        Parameters
        ----------
        bic : dict
            Dictionary containing the biclusters data.
        df : pandas.DataFrame
            Dataframe containing the dataset.
        main_var : dict
            Dictionary containing the main variables' information.
        mode : str
            Mode of the plot. Can be 'categories' or 'coordinates'.
        """
        if mode == 'categories':
            self.plot_parallel_categories(bic,df,main_var,folder_name)
        elif mode == 'coordinates':
            self.plot_parallel_coordinates(bic,df,main_var,folder_name)