# TakeMeter
 
A fine tuned text classifier that evaluates discourse quality in NBA GOAT and legacy debate threads on r/nba.
 
## Community choice and reasoning
 
I chose r/nba, specifically GOAT and legacy debate threads, meaning posts and comments about MJ vs LeBron, Kobe, Magic vs Bird, Wilt, Russell, and similar era comparisons. I picked this because r/nba is large and active, and GOAT debates come up constantly, so there was no shortage of real posts to collect. This community is a good fit for a classification task because the same opinion gets argued in very different ways. Two people can both believe LeBron is the GOAT, but one will back it up with stats, era context, and direct reasoning, while the other just states it with no support. The label is not about which side of the debate someone is on, it is about how developed the argument actually is. The discourse is varied enough to be interesting because it spans many different comparisons rather than one repeated argument, including MJ vs LeBron, Kobe vs LeBron, Magic vs Bird, and era adjusted stat debates, which gave the dataset a wide range of argument styles instead of the same handful of talking points repeated over and over.
 
## Label taxonomy
 
Three labels were used, based on how much actual support is behind a claim, not the tone of the post and not which side of the debate the poster is on.
 
**supported_argument**: A post that makes a claim about who is the GOAT or who is better and backs it up with specific evidence such as stats, seasons, matchups, or era context, or that directly engages with and rebuts another argument.
 
Example 1: Not everything is Lebron vs MJ And is an MVP for Kareem not noteworthy because it didnt exist for Mikan? a DPOY for Jordan because it didnt exist for Wilt? A Finals MVP because it didnt exist for Russell?
 
Example 2: Detailed comparative stats argument citing specific advanced metrics such as points per 100 possessions or true shooting percentage to support a claim about who the better scorer is across eras.
 
**unsupported_take**: A post that states a clear position on the debate but does not back it up with anything beyond a single shallow reason or no reason at all.
 
Example 1: If you havent realized that LeBron is 1b at lowest in the GOAT debate for the foreseeable future I dont know what to tell you.
 
Example 2: Hes the GOAT theres zero debate.
 
**reaction_noise**: A post that is not really making an argument at all. This includes hype, insults, memes, one word replies, rhetorical questions posed to the community without an answer of their own, or content that is off topic from the actual GOAT debate.
 
Example 1: This subreddit isnt for basketball discussion, its for posting top 10 lists and GOAT debates.
 
Example 2: A hypothetical team matchup question such as what team would win, Stockton, Curry, KD, LeBron, Hakeem versus Magic, Kobe, Jordan, Garnett, Shaq, posed to the community with no argument made by the poster.
 
## Data collection
 
### Source
 
Posts and comments were collected from r/nba using pullpush.io, a third party historical Reddit archive that does not require Reddit OAuth credentials. This route was necessary because Reddit closed self service API app creation in 2026 under its Responsible Builder Policy, which made the originally planned PRAW based collection impossible. Data was pulled across fifteen search terms covering GOAT debate, MJ vs LeBron, Jordan vs LeBron, Kobe vs LeBron, Jordan rings argument, Bill Russell GOAT, Wilt Chamberlain greatest, LeBron stats vs rings, Kareem vs LeBron, Jordan vs Kobe, LeBron legacy, Jordan greatest ever, is LeBron overrated, top 10 all time, and Magic vs Bird. Both submissions and their top level comments were collected for each term.
 
### Cleaning process
 
Raw collection across two rounds returned 623 rows. Cleaning removed exact duplicates from overlapping search terms, posts where the body had been removed or deleted by moderators with nothing usable left in the title, and posts that matched a search term incidentally but were not actually GOAT debate discourse, such as post game threads, power rankings, trade rumors, and unrelated long form content like draft coverage or coaching news. This brought the dataset to 419 usable rows.
 
### Labeling process
 
Labeling was done as an AI assisted pre labeling pass followed by a human review step, consistent with the AI Tool Plan in planning.md. Each of the 419 cleaned rows was read individually and assigned a suggested label by applying the three label definitions above along with the edge case rule described below. These suggestions were written into an ai_suggested_label column, kept separate from the final label column, so that human agreement or disagreement could be tracked rather than silently merged. From the 419 labeled rows, a working set of 261 was selected, sampled proportionally across the three labels so that unsupported_take, the smallest class, still met the 50 to 100 example target from planning.md.
 
### Edge case rule applied during labeling
 
A stat only counts as support for the supported_argument label if it is connected to a comparison or reason. A bare stat with no argument attached, such as a post simply listing a players career point total with no further reasoning, was labeled unsupported_take instead. This rule came directly from planning.md and was applied consistently across the dataset.
 
### Label distribution
 
Final dataset of 261 examples.
 
| label | count |
|---|---|
| supported_argument | 137 |
| reaction_noise | 74 |
| unsupported_take | 50 |
 
### Three difficult to label examples
 
**Example 1**: A post listing several real NBA stats and facts, such as career averages and historical team records, with no sentence connecting any of those facts to a GOAT argument. This was the clearest test of the edge case rule. It was labeled unsupported_take rather than supported_argument, because the stats were never used to argue anything, they were just stated.
 
**Example 2**: A short comment stating that the GOAT debate is pointless or unanswerable. This sits between unsupported_take and reaction_noise, since it is commentary on the debate itself rather than a position within it. It was labeled reaction_noise, on the basis that it is not making a claim about who is better, it is meta commentary about the discourse, which fits the off topic criterion in the reaction_noise definition.
 
**Example 3**: A long, well researched post, such as a detailed career evaluation or a custom statistical methodology for ranking players, that takes a clear stance but opens by stating the author is biased against one of the players involved. This was labeled supported_argument despite the stated bias, since the label definition is about whether evidence and reasoning are present, not about whether the author is neutral.
 
## Fine tuning approach
 
### Base model
 
Model Used: llama-3.3-70b-versatile, distilbert-base-uncased
 
### Training setup
 
Training was run in Google Colab on a T4 GPU using the Hugging Face Trainer API. The dataset was split into training and validation sets from the 261 labeled examples. Text was tokenized and the model was fine tuned as a three class sequence classification task corresponding to the three labels above.
 
### Hyperparameter decision: epochs and batch size
 
The first training run used 5 epochs at a batch size of 16. Training loss dropped steadily across all 5 epochs while validation loss stayed flat or rose slightly, which is the standard signature of overfitting on a small dataset. Validation accuracy was also noisy rather than improving, moving between roughly 0.51 and 0.56 across epochs with no clear upward trend. Based on this, epoch count was reduced and the run was repeated, which produced more stable, closely tracking training and validation loss curves, though accuracy did not improve on its own from this change alone.
 
### Hyperparameter decision: class weighting
 
The more significant change was adding class weighting to the loss function. The original unweighted fine tuned model collapsed toward the majority class, predicting supported_argument for nearly every example regardless of true label, which produced 0.00 precision and recall on unsupported_take. This happened because supported_argument made up about 53 percent of the training data, 137 of 261 examples, so a standard unweighted loss function had little incentive to learn the minority classes. A custom Trainer subclass was written to apply inverse frequency class weights inside the loss calculation, so that mistakes on unsupported_take and reaction_noise were penalized more heavily than mistakes on supported_argument. This directly fixed the collapse, restoring real precision and recall on the minority classes, and is the training setup used for the final reported results below.
 
## Baseline description
 
The baseline used the same base model in an untuned, prompted setting rather than a fine tuned one. A system prompt named the community and task, gave the same three label definitions from planning.md including the edge case rule, provided one real example post per label drawn directly from the labeled dataset, and instructed the model to respond with only the label name and no explanation. Baseline results were collected by running this prompt over a held out evaluation set of 40 examples and parsing the models single word response against the three valid label strings. All 40 responses were parseable.
 
## Evaluation report
 
### Baseline accuracy
 
Overall accuracy: 0.625, evaluated on 40 of 40 parseable responses.
 
| label | precision | recall | f1 score | support |
|---|---|---|---|---|
| supported_argument | 0.84 | 0.76 | 0.80 | 21 |
| unsupported_take | 0.40 | 0.75 | 0.52 | 8 |
| reaction_noise | 0.50 | 0.27 | 0.35 | 11 |
 
### Fine tuned model accuracy
 
Overall accuracy: 0.675, evaluated on the same 40 example test set, using the class weighted training setup described above.
 
| label | precision | recall | f1 score | support |
|---|---|---|---|---|
| supported_argument | 0.74 | 0.95 | 0.83 | 21 |
| unsupported_take | 0.56 | 0.62 | 0.59 | 8 |
| reaction_noise | 0.50 | 0.18 | 0.27 | 11 |
 
### Confusion matrix, fine tuned model
 
Rows are true label, columns are predicted label.
 
| true label | predicted supported_argument | predicted unsupported_take | predicted reaction_noise |
|---|---|---|---|
| supported_argument | 20 | 1 | 0 |
| unsupported_take | 1 | 5 | 2 |
| reaction_noise | 6 | 3 | 2 |
 
### Three specific wrong predictions and analysis
 
**Wrong prediction 1**: A true reaction_noise example was predicted as supported_argument. This is the single largest error pattern in the confusion matrix, 6 of the 9 reaction_noise mistakes went to supported_argument. The likely cause is length and structure rather than content. Several reaction_noise examples in this dataset are long, such as anecdotes, nostalgic reflections, or shared links with surrounding commentary, and the model may be using length or the presence of basketball terminology as a weak signal for supported_argument, even when no real comparison or reasoning is present.
 
**Wrong prediction 2**: A true reaction_noise example was predicted as unsupported_take. This matches the original hypothesis written before fine tuning, that reaction_noise and unsupported_take share a fuzzy boundary. A short, dismissive comment that states an opinion in passing, such as a sarcastic aside about the debate itself, can read as a bare unsupported claim depending on phrasing, even when it was labeled reaction_noise because it is not really arguing a position, it is commentary on the discourse.
 
**Wrong prediction 3**: A true unsupported_take example was predicted as reaction_noise. Looking back at the original annotation for similar posts, this points to a genuine annotation inconsistency rather than a clean model failure. Some short, bare assertions in the dataset were labeled unsupported_take, for example a one line GOAT verdict with no support, while other similarly short, bare assertions were labeled reaction_noise, for example a one line dismissive comment. Both are short and low on argumentative content, and the line between them depended on a subjective read of whether the poster was stating a position versus just reacting, which was not always applied with a fully consistent rule.
 
### What would need to change to fix the reaction_noise weakness
 
Reaction_noise has the weakest recall of all three labels even after class weighting, 0.18, only 2 of 11 correct. The likely explanation is that the label itself is heterogeneous. It currently covers several distinct kinds of content, including memes, off topic tangents, rhetorical questions, hype, and complaints about the subreddit, which do not share one consistent textual pattern the way supported_argument does with stats and comparison language. More training examples alone would likely help only partially. A more direct fix would be tightening the label definition or splitting reaction_noise into narrower sublabels, for example separating off topic content from low effort on topic reactions, so that each label has a more learnable, consistent signature.
 
### Sample classifications
 
Three posts were run directly through the fine tuned model outside the test set evaluation pipeline, to show predicted label and confidence in a format closer to how the model would actually be used.
 
| post text excerpt | predicted label | confidence |
|---|---|---|
| Not everything is Lebron vs MJ And is an MVP for Kareem not noteworthy because it didn't exist for Mikan... | supported_argument | 34.8% |
| He's the GOAT there's zero debate. | unsupported_take | 38.2% |
| This subreddit isn't for basketball discussion, it's for posting top 10 lists and GOAT debates | reaction_noise | 35.7% |
 
All three predictions in this sample are correct, matching the labels these posts were originally given during annotation. Worth noting honestly, none of these predictions are made with high confidence, all three sit in the mid 30 percent range, only somewhat above the roughly 33 percent a random guess would get across three classes. The unsupported_take example, He's the GOAT there's zero debate, is the clearest one to explain. It states a position with no evidence or reasoning attached, which is exactly the unsupported_take definition, no stats, no comparison, no engagement with a counterargument, just a bare verdict. The model got the label right, but the low confidence score suggests it is picking up on the right pattern weakly rather than strongly, likely because a five word post gives it very little text to work with, which lines up with the same short post weakness seen in the wrong predictions above.
 
## Reflection, what the model learned versus what was intended
 
The model learned a strong, generalizable pattern for supported_argument, picking up on stat heavy, comparison heavy language fairly reliably, which matches the intent behind that label. It also learned a real, if weaker, pattern for unsupported_take once class weighting corrected the initial majority class collapse. What it did not learn well is the intended distinction at the edges of reaction_noise, where the definition asks the model to recognize an absence of argument across several very different surface forms. The intended label was a single coherent category, not really an argument, but in practice the model seems to be treating reaction_noise as closer to a fallback or default for short, ambiguous text, which is a narrower and less accurate version of what the label was meant to capture.
 
## Spec reflection
 
One way the spec helped was the instruction to read 30 to 40 real posts before writing label definitions. Reading the actual text surfaced patterns that were not obvious in the original problem statement, for example that a post can list real basketball statistics without using them to argue anything, which directly led to the edge case rule for supported_argument. Writing that rule down before annotating 200 plus examples kept labeling decisions consistent later on.
 
One way implementation diverged from the original plan was the data collection method. Planning.md specified PRAW for collection. Reddit closed self service API access partway through this project under a new policy, which made that path unworkable. Collection was redone using pullpush.io, a third party archive that does not require Reddit OAuth credentials. This changed nothing about the label design or annotation process, but it did mean accepting a data source with some lag and occasional reliability issues, including comment search timeouts on a subset of search terms, which had to be retried separately.
 
## AI usage
 
AI assistance was used throughout this project in ways that go beyond general advice, and is disclosed specifically here rather than only in planning.md.
 
**Instance 1, label stress testing during annotation**: While labeling, Claude flagged several rows as ambiguous fits for any of the three labels rather than forcing a label, including AI generated content such as a rap battle written by a language model, and exact or near duplicate posts that had been collected twice under different search terms. These were marked for removal rather than labeled, and that removal decision was carried forward into the final 261 example dataset rather than being overridden.

## Demo Link:
https://youtu.be/0fsMFa-6irE
 
**Instance 2, training diagnosis**: When the first fine tuned model produced 0.00 precision and recall on unsupported_take, Claude was directed to read the confusion matrix and propose a cause rather than just suggest hyperparameter changes blindly. The diagnosis was class imbalance causing majority class collapse, which led to a class weighted Trainer subclass. This fix was implemented, tested, and confirmed against a new confusion matrix rather than assumed to have worked from the loss curves alone.
