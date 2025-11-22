import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle

data = pd.read_csv("student_data.csv")

X = data[["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8","Attendance","Assignments"]]
y = data["Performance"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=150, random_state=42)
model.fit(X_train, y_train)

pickle.dump(model, open("student_model.pkl", "wb"))
print("Model trained and saved as student_model.pkl")
print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")
print(f"Classes: {model.classes_}")
