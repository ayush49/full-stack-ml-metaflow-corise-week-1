from metaflow import (
    FlowSpec,
    step,
    Flow,
    current,
    Parameter,
    IncludeFile,
    card,
    current,
)
from metaflow.cards import Table, Markdown, Artifact

# TODO move your labeling function from earlier in the notebook here
labeling_function = lambda row: 1 if row['rating']>=4 else 0


class BaselineNLPFlow(FlowSpec):
    # We can define input parameters to a Flow using Parameters
    # More info can be found here https://docs.metaflow.org/metaflow/basics#how-to-define-parameters-for-flows
    split_size = Parameter("split-sz", default=0.2)
    # In order to use a file as an input parameter for a particular Flow we can use IncludeFile
    # More information can be found here https://docs.metaflow.org/api/flowspec#includefile
    data = IncludeFile("data", default="../data/Womens Clothing E-Commerce Reviews.csv")

    @step
    def start(self):
        # Step-level dependencies are loaded within a Step, instead of loading them
        # from the top of the file. This helps us isolate dependencies in a tight scope.
        import pandas as pd
        import io
        from sklearn.model_selection import train_test_split

        # load dataset packaged with the flow.
        # this technique is convenient when working with small datasets that need to move to remove tasks.
        df = pd.read_csv(io.StringIO(self.data))

        # filter down to reviews and labels
        df.columns = ["_".join(name.lower().strip().split()) for name in df.columns]
        df["review_text"] = df["review_text"].astype("str")
        _has_review_df = df[df["review_text"] != "nan"]
        reviews = _has_review_df["review_text"]
        labels = _has_review_df.apply(labeling_function, axis=1)
        # Storing the Dataframe as an instance variable of the class
        # allows us to share it across all Steps
        # self.df is referred to as a Data Artifact now
        # You can read more about it here https://docs.metaflow.org/metaflow/basics#artifacts
        self.df = pd.DataFrame({"label": labels, **_has_review_df})
        del df
        del _has_review_df

        # split the data 80/20, or by using the flow's split-sz CLI argument
        _df = pd.DataFrame({"review": reviews, "label": labels})
        self.traindf, self.valdf = train_test_split(_df, test_size=self.split_size)
        print(f"num of rows in train set: {self.traindf.shape[0]}")
        print(f"num of rows in validation set: {self.valdf.shape[0]}")

        self.next(self.baseline)

    @step
    def baseline(self):
        "Compute the baseline"

        ### TODO: Fit and score a baseline model on the data, log the acc and rocauc as artifacts.

        ###

        import pandas as pd
        from sklearn.model_selection import train_test_split
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, roc_curve, auc

        X_train = self.traindf['review']
        y_train = self.traindf['label']

        X_test = self.valdf['review']
        y_test = self.valdf['label']    

        tfidf_vectorizer = TfidfVectorizer(max_features=5000)
        X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
        X_test_tfidf = tfidf_vectorizer.transform(X_test)

        # Step 2: Model Selection and Training
        model = LogisticRegression()
        model.fit(X_train_tfidf, y_train)

        # Step 3: Model Evaluation
        y_pred = model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)

        # Step 4: ROC AUC Calculation
        y_prob = model.predict_proba(X_test_tfidf)[:, 1]  # Probability of the positive class
        roc_auc = roc_auc_score(y_test, y_prob)


        ###
        self.base_acc = accuracy
        self.base_rocauc = roc_auc

        self.next(self.end)

    @card(
        type="corise"
    )  # TODO: after you get the flow working, chain link on the left side nav to open your card!
    @step
    def end(self):
        msg = "Baseline Accuracy: {}\nBaseline AUC: {}"
        print(msg.format(round(self.base_acc, 3), round(self.base_rocauc, 3)))

        current.card.append(Markdown("# Womens Clothing Review Results"))
        current.card.append(Markdown("## Overall Accuracy"))
        current.card.append(Artifact(self.base_acc))

        current.card.append(Markdown("## Examples of False Positives"))
        # TODO: compute the false positive predictions where the baseline is 1 and the valdf label is 0.
        # TODO: display the false_positives dataframe using metaflow.cards
        # Documentation: https://docs.metaflow.org/api/cards#table

        current.card.append(Markdown("## Examples of False Negatives"))
        # TODO: compute the false positive predictions where the baseline is 0 and the valdf label is 1.
        # TODO: display the false_negatives dataframe using metaflow.cards


if __name__ == "__main__":
    BaselineNLPFlow()
