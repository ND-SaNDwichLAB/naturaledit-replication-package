# NaturalEdit Replication Package

This repository contains the replication package for the paper "NaturalEdit: Code Modification through Direct Interaction with Adaptive Natural Language Representation." Please note that the content already included in the paper appendix is not repeated here. The package is organized as follows (with key folders and files described):

- **`naturaledit-extension/`**  
  Source code for the NaturalEdit VS Code extension.

- **`baseline-extension/`**  
  Source code for the Baseline VS Code extension used in the user study.

- **`evaluation-showcase/`**
  Source code for the technical evaluation showcase website, including the interface used to assist expert ratings and the interactive demo for evaluating individual data points in the benchmark. **Deployed at [www.nztang.com/naturaledit-evaluation-showcase/](https://www.nztang.com/naturaledit-evaluation-showcase/), please take a look!**.

- **`benchmark-results/`**  
  Materials for the benchmark evaluation, including all model outputs and evaluation scripts.
  - `data/`: Original benchmark datasets.
  - `output/`: Model outputs and evaluation results on the benchmark datasets.
    - `combined/`: Cleaned outputs, prepared for the evaluation showcase.
  - `figure/`: Figures about benchmark results presented in the paper.
  - `infer_naturaledit.py`: Script to run NaturalEdit APIs on the benchmark datasets.
  - `evaluate_correctness.py`: Script to evaluate correctness of the generated outputs.
  - `run_results.ipynb`: Jupyter notebook that uses the above scripts to reproduce benchmark results.
  - `visualization.ipynb`: Script to visualize benchmark results.

- **`expert-ratings/`**  
  Materials for expert ratings of intermediate representations.
  - `mapping.pdf`: Anonymized expert ratings for mapping quality, including each expert's initial ratings, the final ratings after discussion, and the aggregated results.
  - `summary_diff.pdf`: Anonymized expert ratings for the summary quality and diff quality, with same content as above.
  - `preparation/`: Scripts used to prepare the raw data for expert rating tasks.
  - `analysis/`: Scripts used to analyze the expert ratings.
    - `data/`: Raw and processed data used by the analysis scripts.
    - `agreement.ipynb`: Jupyter notebook that computes inter-rater agreement.
    - `visualization.py`: Script to visualize expert ratings.

- **`study-tasks/`**  
  Programming tasks used in the study. Deployed in CodeSandbox, where you can play with the tasks and the extensions:
  1. Finance Dashboard: https://codesandbox.io/p/devbox/6hf2dg
  2. MVP Predictor: https://codesandbox.io/p/devbox/3h6s9l
  - `buggy-code/`: Initial code given to participants.
  - `ground-truth/`: Reference solutions.
  - `setup/`: Setup files for CodeSandbox environments.
  - `naturaledit.vsix`: Compiled VSIX file of the NaturalEdit extension.
  - `edithelper.vsix`: Compiled VSIX file of the Baseline extension.

- **`qualitative-analysis/`**  
  Materials for qualitative analysis of the user study.
  - `coded_quotes.csv`: Anonymized, coded interview segments.

- **`quantitative-analysis/`**  
  Materials for quantitative analysis of the user study.
  - `download/`: Scripts for downloading raw interaction logs from the Firebase.
  - `interactions/`: JSON files of each participant's interaction logs.
    - `naturaledit_cleaned.csv`: Cleaned interaction logs for NaturalEdit.
    - `baseline_cleaned.csv`: Cleaned interaction logs for Baseline.
  - `questionnaires/`: TXT files of participants' responses to user study questionnaires and performance records.
    - `post_task.txt`: Post-task questionnaire responses.
    - `post_study.txt`: Post-study questionnaire responses.
    - `task_record.txt`: Participants' task completion time records.
  - `figures/`: Result figures presented in the paper.
  - `anly_questionnaires.ipynb`: Jupyter notebook that uses the Python scripts `anly*.py` in this folder to reproduce quantitative analysis results, including task performance and Likert-scale analysis.
  - `anly_interactions.ipynb`: Jupyter notebook that preprocesses, cleans, analyzes, and visualizes interaction logs.
  - `anly_*.py`: Python scripts that analyze participant questionnaires responses.
  - `vis_*.py`: Python scripts that visualize likert-scale results.