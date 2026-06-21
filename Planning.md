TakeMeter — Planning

Community

I picked r/nba, specifically GOAT/legacy debate threads (Jordan vs. LeBron, Kobe, Magic vs. Bird, "is X a top 10 player ever"). I went with this because it's one of the biggest, most active subreddits out there, so there's no shortage of posts to pull from, and GOAT debates specifically come up constantly.

This is a good fit for a classification task because the same opinion gets argued in totally different ways. Two people can both think "LeBron is the GOAT," but one of them will back it up with stats, era context, and a real argument, while the other just says "LeBron is just better, that's it" and leaves it there. So the label isn't about which side someone's on, it's about how they're arguing it — which is exactly the kind of distinction a classifier needs to learn.

The discourse is varied enough to be interesting because there isn't just one comparison, theres multiple; some of the most common debates are MJ vs. LeBron, but also Kobe vs. LeBron, Magic vs. Bird, "top 10 all time" lists, etc. That means I'm not just scraping the same 10 arguments over and over, I'm getting a real range of how people argue, from well-thought-out breakdowns to quick gut reactions.

Labels

I'm using 3 labels, based on how much actual support is behind the claim, not the tone of the post and not which side of the debate someone is on.

1. Supported argument — A post that makes a claim about who's the GOAT (or who's better) and backs it up with real evidence, like specific stats, seasons, matchups, or era context, or that directly responds to and engages with someone else's argument.

Example 1: [PASTE REAL EXAMPLE — should be a post/comment that cites specific stats, seasons, or context to support a GOAT claim, e.g. comparing peak years, playoff performance in specific years, surrounding talent, etc.]

Example 2: [PASTE REAL EXAMPLE — a rebuttal-style comment that responds directly to another comment's point with counter-evidence, not just disagreement]

2. Unsupported take — A post that states a clear position on the debate but doesn't back it up with anything beyond a single shallow reason or no reason at all (e.g. just "rings" with nothing else, or "X is just better, no debate").

Example 1: "I feel MJ was the better on ball for sure but Lebron was a fantastic team defender in his prime. Great help defender, could switch on multiple positions for a possession when needed, and he could read and disrupt opposition offences really well at times. His ridiculous athletic blocks were dope too lol."

Example 2: "Jordan without question. Better on ball defender with quick hands and anticipation. Jordan even has more steals than lebron when having played 7-8 less seasons lol"

3. Reaction/noise — A post that isn't really making an argument at all — pure hype, an insult, a meme reference, a one-word reply, or something off-topic to the actual debate.

Example 1: "MJ all day"

Example 2: "Bron da goat"

Example 3: "Jordan was better at defending guards, Bron better at defending anything."

Hard edge cases

The most ambiguous case is going to be a post that throws out a stat but doesn't actually connect it to an argument. Something like "LeBron has 40,000 points" on its own — that's a real number, so it might look like it belongs in "supported argument," but if the person never explains why that stat means LeBron is better (no comparison, no context, nothing), it's really just restating a fact, which is closer to an unsupported take.

My rule for handling this during annotation: a stat only counts as "supported" if it's connected to a comparison or a reason — the post has to actually use the stat to argue something, not just drop it. If I read a post and can't point to the sentence where the stat turns into an argument, it goes in "unsupported take," not "supported argument." I'll keep a running log of these borderline calls as I annotate so I can stay consistent across all 200 posts instead of making a different judgment call each time.

Data collection plan

I'll collect from r/nba, mainly from GOAT-debate posts and the top comments on those posts, using search terms like "GOAT debate," "MJ vs LeBron," "Kobe vs LeBron," "is LeBron overrated," "top 10 all time," etc.

I'm aiming for 50–100 examples per label (around 200+ total). If a label is underrepresented after I hit 200 total examples — which I'd guess will probably be "supported argument," since real arguments are rarer than quick reactions, I'll go back and search more targeted terms to find that type of post specifically.

Evaluation metrics

Accuracy alone isn't enough here because my labels probably won't be evenly distributed if "reaction/noise" or "unsupported take" end up being a much bigger chunk of the data than "supported argument," a model could get a high accuracy score just by guessing the majority label every time and basically never learning to recognize a real supported argument.

Accounting for this, I'll use precision and recall per label, not just overall accuracy. I want to know specifically how often the model correctly catches a "supported argument" (recall) and how often it's right when it predicts that label (precision), since that's the label I care most about it getting right.
F1 score per label, to balance precision and recall into one number I can compare across labels.
A confusion matrix, so I can actually see which labels are getting mixed up with each other — like if "unsupported take" and "supported argument" are getting confused a lot, that tells me my boundary rule (the stat-connection rule above) isn't being learned well, which is more useful to know than just an overall score.


Definition of success

I'd consider this genuinely useful if the model can correctly tell "supported argument" apart from "unsupported take" most of the time, since that's the actual hard distinction this whole project is about — telling reaction/noise apart from the other two should be the easier part.

For "good enough," I'd want at least around 75–80% F1 on each label, and I'd want the confusion matrix to show that mistakes are mostly happening on genuinely borderline posts (the kind I struggled with myself during annotation) rather than on clear-cut cases. If it's mixing up an obvious meme reply with a well-supported argument, that's a real failure. If it's mixing up two posts that even I had to think twice about, that's a more reasonable kind of mistake and I'd accept that as good enough for a first version of this tool.

AI Tool Plan:

Label stress-testing:

Before I start labeling all 200+ posts, I'm going to take my label definitions and my edge case rule and ask an AI tool to generate 5–10 fake GOAT-debate posts that are designed to sit right on the boundary between two labels: mainly supported argument vs. unsupported take. Then, I'll try to classify each one myself using only my written definitions, without explaining anything extra in my head that isn't actually written down. If I can't confidently and consistently place one of these generated posts into a single label, that means my definition has a gap, not that the example is just "a hard one" — so I'll go back and tighten the wording of the label or the edge case rule before I touch my real data. I want to do this stress test first, because it's a lot cheaper to fix a fuzzy definition now than to discover it 120 posts into annotating.

Annotation Assistance:

I'm going to use an LLM (Claude) to pre-label my full batch of 200+ collected posts before I go through and review them myself. I won't just trust the AI labels as-is. I'll give it my exact label definitions and the edge case rule from this document, have it assign one of the three labels to each post, and then I'll personally go through every single one and either confirm or correct it.

Failure Analysis:

Once I've trained the classifier and run it on my held-out test set, I'll pull the list of examples it got wrong and hand that list to an AI tool to look for patterns — things like: is it consistently confusing one specific label pair (like my supported-vs-unsupported boundary), is it failing more on short posts vs. long ones, is it tripped up by sarcasm, or is it failing more on one specific GOAT comparison (like Kobe vs. LeBron posts) than others.

I won't just take the AI's pattern summary and put it straight into my evaluation writeup, though. For each pattern it claims to find, I'll go back to the actual misclassified posts myself and check whether the pattern really holds up across a meaningful number of them, not just one or two examples that happen to fit the story. If a "pattern" only explains 2 out of 15 errors, I'll say so in my writeup instead of overstating it — the point of this step is to give me a starting place to look, not a finished conclusion.


