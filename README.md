# parkrun
This is a collection of simple functions in Python to manipulate and analyse parkrun data.

The library requires pandas and matplotlib to work.

## Simple usage
    import parkrun
    infile = r'.\data\Parkrun_Woodhouse_Results_458_04062016.txt'
    results = parkrun.importResults(infile,report=True)

The input data should contain a dump of the table of results as published on the parkrun website. Just copy and paste the entire content of the page in a text file.
The function will assume that the headers and footers are in the file and the right number of lines to skip can be set in the function.

To show descriptive statistics of the results, type:

    parkrun.print_stats(results)
    
A bar plot of the number of runners in each age category can be obtained with:

    parkrun.plot_AgeCat(results)
    
