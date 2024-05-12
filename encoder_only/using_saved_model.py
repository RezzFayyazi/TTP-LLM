# -*- coding: utf-8 -*-
"""using_saved_model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1HRsVlfPf63hZRNA4e4YC4_KCvAl2VBP-
"""
"""
!pip install -q transformers datasets
!pip install pytorch-lightning
!pip install -q git+https://github.com/huggingface/peft.git
"""
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from datasets import load_dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, roc_auc_score, accuracy_score

from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
from transformers import TrainingArguments, Trainer
from transformers import EvalPrediction


from google.colab import drive
drive.mount('/content/drive')

dataset = load_dataset('csv', data_files={'train': ['/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/data/cleaned_data_for_multiclassification_task/cleaned_shuffled_new_MITRE.csv',],
                                          })
labels = [label for label in dataset['train'].features.keys() if label not in ['ID', 'Description']]
labels = sorted(labels)

id2label = {idx:label for idx, label in enumerate(labels)}
label2id = {label:idx for idx, label in enumerate(labels)}
labels

#use saved model
model_path = ('/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/trained_models/new_MITRE_dataset/roberta-base_30epochs_16b_5e-5L')

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

test_set = pd.read_csv('/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/data/testing_data/Y-MITRE_Procedures.csv')

#correct the format
test_set['Tactics'] = test_set.apply(lambda x: ', '.join(sorted([value for value in x[['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4']] if pd.notnull(value)])), axis=1)
test_set.drop(['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4'], axis=1, inplace=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.to(device)

data = []

for i in range(len(test_set["Procedures"])):
    text = test_set['Procedures'][i]

    encoding = tokenizer(text, return_tensors="pt")
    encoding = {k: v.to(device) for k, v in encoding.items()}

    with torch.no_grad():
        outputs = model(**encoding)
    logits = outputs.logits

    sigmoid = torch.nn.Sigmoid()
    probs = sigmoid(logits.squeeze().cpu())

    predictions = np.zeros(probs.shape)
    predictions[np.where(probs >= 0.5)] = 1

    predicted_labels = [id2label[idx] for idx, label in enumerate(predictions) if label == 1.0]

    keys_with_value_1 = test_set['Tactics'][i]

    data.append({'Description': text, 'Predicted_Labels': ', '.join(predicted_labels), 'Actual_labels': keys_with_value_1})

df = pd.DataFrame(data)
df

new_df = df.copy()
new_df['Predicted_Labels'] = new_df['Predicted_Labels'].apply(lambda x: ', '.join(sorted(x.split(', '))))
new_df['Predicted_Labels'] = new_df['Predicted_Labels'].str.upper()

for i in range(len(new_df['Predicted_Labels'])):
    if len(new_df['Predicted_Labels'][i].split(', ')) != 1:
        labels = new_df['Predicted_Labels'][i].split(', ')
        modified_labels = [label.replace(' ', '_') for label in labels]
        new_df['Predicted_Labels'][i] = ', '.join(modified_labels)
    else:
      new_df['Predicted_Labels'][i] = new_df['Predicted_Labels'][i].replace(' ', '_')
new_df

# Compare "Predicted_Labels" and "Keys_with_1" columns
new_df['Match'] = new_df['Predicted_Labels'] == new_df['Actual_labels']

# Find rows where they are not the same
mismatched_rows = new_df[~new_df['Match']]

# Count the number of mismatched rows
mismatch_count = len(mismatched_rows)

# Print the mismatched rows and the count
if mismatch_count > 0:
    print("Mismatched Rows:")
    print(mismatched_rows)
    print(f"Total Mismatched Rows: {mismatch_count}")
else:
    print("No mismatches found.")
new_df.to_csv('/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/testing_procedures_final_shuffled/secure_bert/predicted_labels_with_30epochs_0.4.csv', index=False)

from sklearn.metrics import classification_report
import math


test_set = pd.read_csv('/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/data/testing_data/Y-MITRE_Procedures.csv')
test_set = test_set.drop(columns=['URL'])
#test_set.rename(columns={'Technique_ID': 'ID'}, inplace=True)

unique_tactic_names = pd.Series(test_set['Tactic1'].tolist() + test_set['Tactic2'].tolist() + test_set['Tactic3'].tolist() + test_set['Tactic4'].tolist()).unique()
my_list = [x for x in unique_tactic_names if (isinstance(x, str) or not math.isnan(x))]
Tactic_column = ['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4']
for name in my_list:
  test_set[name] = 0

for i in range(len(test_set)):
  for tactic in Tactic_column:
    if pd.notna(test_set[tactic].iloc[i]):
      test_set[test_set[tactic].iloc[i]].iloc[i] = 1
test_set = test_set.drop(columns=['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4'], axis=1)
print(test_set)
# data = []
for testing_number in range(1, 2):
  df_predicted = pd.DataFrame(columns = test_set.columns[1:])
  for i in range(len(test_set['Procedures'])):


    text = test_set['Procedures'][i]

    encoding = tokenizer(text, return_tensors="pt")
    encoding = {k: v.to(trainer.model.device) for k,v in encoding.items()}

    outputs = trainer.model(**encoding)
    logits = outputs.logits

    sigmoid = torch.nn.Sigmoid()
    probs = sigmoid(logits.squeeze().cpu())

    predictions = np.zeros(probs.shape)
    predictions[np.where(probs >= 0.5)] = 1
    predictions[np.where(probs < 0.5)] = 0
    df_predicted.loc[len(df_predicted)] = predictions
      #predicted_labels = [id2label[idx] for idx, label in enumerate(predictions) if label == 1.0]

        # keys_with_value_1 = test_set['Tactics'][i]
        # data.append({'Description': text, 'Predicted_Labels': ', '.join(predicted_labels), 'Actual_labels': keys_with_value_1})

    # df = pd.DataFrame(data)

    # new_df = df.copy()
    # new_df['Predicted_Labels'] = new_df['Predicted_Labels'].apply(lambda x: ', '.join(sorted(x.split(', '))))
    # new_df['Predicted_Labels'] = new_df['Predicted_Labels'].str.upper()

    # for i in range(len(new_df['Predicted_Labels'])):
    #     if len(new_df['Predicted_Labels'][i].split(', ')) != 1:
    #         labels = new_df['Predicted_Labels'][i].split(', ')
    #         modified_labels = [label.replace(' ', '_') for label in labels]
    #         new_df['Predicted_Labels'][i] = ', '.join(modified_labels)
    #     else:
    #         new_df['Predicted_Labels'][i] = new_df['Predicted_Labels'][i].replace(' ', '_')

    # new_df['Match'] = new_df['Predicted_Labels'] == new_df['Actual_labels']
    # mismatched_rows = new_df[~new_df['Match']]
    # mismatch_count = len(mismatched_rows)
    # if mismatch_count > 0:
    #     print("Mismatched Rows:")
    #     print(mismatched_rows)
    #     print(f"Total Mismatched Rows: {mismatch_count}")
    # else:
    #     print("No mismatches found.")

    # Save the DataFrame with a unique file name based on the testing number
    # predicted_labels = new_df['Predicted_Labels'].tolist()
    # actual_labels = new_df['Actual_labels'].tolist()
    # report = classification_report(actual_labels, predicted_labels, output_dict=True)
    # report_df = pd.DataFrame(report).transpose()

  # class_names = df_predicted.columns.tolist()
  # test_set_report = test_set.drop(columns='Procedures')
  # y_true = test_set_report.values
  # y_pred = df_predicted.values
  # report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
  # report = pd.DataFrame(report).transpose()

  # # Define the file paths with the testing number in the file names
  # result_file_path = f"/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/final_testing_10times/roberta_base/predicted_labels_{testing_number}.csv"
  # report_file_path = f"/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/final_testing_10times/roberta_base/df_report_{testing_number}.csv"
  # report_df_path = f"/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/final_testing_10times/roberta_base/classification_report_{testing_number}.csv"
  # #new_df.to_csv(result_file_path, index=False)
  # #report_df.to_csv(report_file_path, index=True)
  # report.to_csv(report_df_path, index=True)



from sklearn.metrics import classification_report
import math
from sklearn.metrics import accuracy_score


test_set = pd.read_csv('/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/data/testing_data/Y-MITRE_Procedures.csv')
test_set = test_set.drop(columns=['URL'])
unique_tactic_names = pd.Series(test_set['Tactic1'].tolist() + test_set['Tactic2'].tolist() + test_set['Tactic3'].tolist() + test_set['Tactic4'].tolist()).unique()
my_list = [x for x in unique_tactic_names if (isinstance(x, str) or not math.isnan(x))]
Tactic_column = ['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4']
for name in my_list:
  test_set[name] = 0

for i in range(len(test_set)):
  for tactic in Tactic_column:
    if pd.notna(test_set[tactic].iloc[i]):
      test_set[test_set[tactic].iloc[i]].iloc[i] = 1

test_set['Tactics'] = test_set.apply(lambda x: ', '.join(sorted([value for value in x[['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4']] if pd.notnull(value)])), axis=1)
test_set.drop(['Tactic1', 'Tactic2', 'Tactic3', 'Tactic4'], axis=1, inplace=True)

desired_order = ['Procedures', 'COLLECTION', 'COMMAND_AND_CONTROL', 'CREDENTIAL_ACCESS',
 'DEFENSE_EVASION', 'DISCOVERY', 'EXECUTION', 'EXFILTRATION', 'IMPACT', 'INITIAL_ACCESS',
 'LATERAL_MOVEMENT', 'PERSISTENCE', 'PRIVILEGE_ESCALATION', 'RECONNAISSANCE', 'RESOURCE_DEVELOPMENT', 'Tactics']



# Reindex the DataFrame with the desired column order
test_set = test_set.reindex(columns=desired_order)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.to(device)


for testing_number in range(1, 11):
    data = []
    df_predicted = pd.DataFrame(columns = test_set.columns[1:-1])
    for i in range(len(test_set["Procedures"])):

        text = test_set['Procedures'][i]

        encoding = tokenizer(text, return_tensors="pt")
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = model(**encoding)
        logits = outputs.logits

        sigmoid = torch.nn.Sigmoid()
        probs = sigmoid(logits.squeeze().cpu())

        predictions = np.zeros(probs.shape)
        predictions[np.where(probs >= 0.5)] = 1
        df_predicted.loc[len(df_predicted)] = predictions
        predicted_labels = [id2label[idx] for idx, label in enumerate(predictions) if label == 1.0]

        keys_with_value_1 = test_set['Tactics'][i]
        data.append({'Description': text, 'Predicted_Labels': ', '.join(predicted_labels), 'Actual_labels': keys_with_value_1})

    df = pd.DataFrame(data)

    new_df = df.copy()
    new_df['Predicted_Labels'] = new_df['Predicted_Labels'].apply(lambda x: ', '.join(sorted(x.split(', '))))
    new_df['Predicted_Labels'] = new_df['Predicted_Labels'].str.upper()

    for i in range(len(new_df['Predicted_Labels'])):
        if len(new_df['Predicted_Labels'][i].split(', ')) != 1:
            labels = new_df['Predicted_Labels'][i].split(', ')
            modified_labels = [label.replace(' ', '_') for label in labels]
            new_df['Predicted_Labels'][i] = ', '.join(modified_labels)
        else:
            new_df['Predicted_Labels'][i] = new_df['Predicted_Labels'][i].replace(' ', '_')

    new_df['Match'] = new_df['Predicted_Labels'] == new_df['Actual_labels']
    mismatched_rows = new_df[~new_df['Match']]
    mismatch_count = len(mismatched_rows)
    if mismatch_count > 0:
        print("Mismatched Rows:")
        print(mismatched_rows)
        print(f"Total Mismatched Rows: {mismatch_count}")
    else:
        print("No mismatches found.")

    # Save the DataFrame with a unique file name based on the testing number
    predicted_labels = new_df['Predicted_Labels'].tolist()
    actual_labels = new_df['Actual_labels'].tolist()
    report = classification_report(actual_labels, predicted_labels, output_dict=True)
    report_df = pd.DataFrame(report).transpose()

    class_names = df_predicted.columns.tolist()
    test_set_report = test_set.drop(columns=['Procedures', 'Tactics'])
    y_true = test_set_report.values
    y_pred = df_predicted.values
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    report = pd.DataFrame(report).transpose()
    accuracy = accuracy_score(y_true, y_pred)
    report.loc['accuracy'] = accuracy

    # Define the file paths with the testing number in the file names
    result_file_path = f"/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/final_testing_10times/roberta_base/predicted_labels_{testing_number}.csv"
    report_file_path = f"/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/final_testing_10times/roberta_base/c_report_{testing_number}.csv"
    report_path = f"/content/drive/MyDrive/projects/finetuning_LLMs_with_MIRTE_data/result_of_testing/final_testing_10times/roberta_base/classification_report_{testing_number}.csv"

    new_df.to_csv(result_file_path, index=False)
    report_df.to_csv(report_file_path, index=True)
    report.to_csv(report_path, index=True)

accuracy = accuracy_score(y_true, y_pred)
accuracy
