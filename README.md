# Python scoring methods for Janka Score

## Description
This repo contains Python code developed for research and simulation of the scoring algorithm developed for Janka Score, my team's hackathon project
developed for ETH Denver 2023. Janka Score is a "credit score" for DeFi Lending based on a modified version of bayesian inference and a beta distribution.
The principal is to infer from on chain lending events (deposit, borrow, repay, liquidate, withdraw), what the probability of repayment of lent capital
will be acheived without having to resort to liquidation. In effect, the "Janka Score", approximates the how risky a DeFi borrower is to lend to.
As liquidations pose a cost to borrowers, and certainly pose a risk to lenders (be it excution, slippage, or liquidity risks), measure the risk of needing liquidations is
important for improving capital efficiency in DeFi.

In this repo, Python code was developed to both simulate scoring, and determine initial parameters used for the ETH Denver 2023 release of Janka score.

## Structure

```
├── README.md          <- The top-level README for developers using this project.
│
├── example_jsons      <- Json files pulled from Messari's AAVE V3 subgraph, used to produce example outputs from model.  
│
├── refined_ruleset    <- Code and Jupyter Notebooks used for Simulations and Research around Janka Score explored in Whitepaper.  
│   └── lib            <- Code for model schema, parameters, and obligor data structures.  
│   └── notebooks      <- Jupyter Notebooks for showing example scoring and Fitting Parameters used for initial model release.  
│
├── testData           <- Jsons used to test model score outputs that were tied with deployment version developed in typescript
```

## Development
1. Clone repo
```
git clone git@github.com:rashadalh/janka_python_scoring.git
```

2. Using Jupyter, to see the code in action consider running
For examples
```
https://github.com/rashadalh/janka_python_scoring/blob/main/refined_ruleset/src/notebooks/Computing%20Example%20Score.ipynb
```
For how initial parameters were determined
```
https://github.com/rashadalh/janka_python_scoring/blob/main/refined_ruleset/src/notebooks/Fitting%20parameters.ipynb
```

## Contact
Rashad Haddad - @rashadalh  

## Link to repo on ETH Denver 2023 Janka Score Hackathon Submission
```
https://github.com/jankascore/scoring_python_apis
```


