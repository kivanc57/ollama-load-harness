LONG_CONTEXT = """
Linguistic relativity asserts that language influences worldview or cognition. One form of linguistic relativity, linguistic determinism, regards peoples' languages as determining and influencing the scope of cultural perceptions of their surrounding world.

Various colloquialisms refer to linguistic relativism: the Whorf hypothesis; the Sapir–Whorf hypothesis (/səˌpɪər ˈhwɔːrf/ sə-PEER WHORF); the Whorf–Sapir hypothesis; and Whorfianism.

The hypothesis is disputed, with many different variations throughout its history.The strong hypothesis of linguistic relativity, now referred to as linguistic determinism, is that language determines thought and that linguistic categories limit and restrict cognitive categories. This was a claim by some earlier linguists pre-World War II; since then it has fallen out of acceptance by contemporary linguists. Nevertheless, research has produced positive empirical evidence supporting a weaker version of linguistic relativity: that a language's structures influence a speaker's perceptions, without strictly limiting or obstructing them.

Although common, the term Sapir–Whorf hypothesis is sometimes considered a misnomer for several reasons. Edward Sapir (1884–1939) and Benjamin Lee Whorf (1897–1941) never stated their ideas in terms of a hypothesis. The distinction between a weak and a strong version of this hypothesis is also a later development; Sapir and Whorf never used such a dichotomy, although often their writings and their opinions of this relativity principle expressed it in stronger or weaker terms.

The principle of linguistic relativity and the relationship between language and thought has also received attention in varying academic fields, including philosophy, psychology and anthropology. It has also influenced works of fiction and the invention of constructed languages.

Source: Wikipedia excerpt on linguistic relativity.
"""


WORKLOADS = {
    "short_prompt_short_output":
    {
        "name": "short_prompt_short_output",
        "num_predict": 32,
        "prompt": "What is 2 + 2? Answer in one sentence.",
        "prompt_category": "short",
        "output_category": "short",
    },

    "short_prompt_long_output":
    {
        "name": "short_prompt_long_output",
        "num_predict": 256,
        "prompt": "Explain the difference between CPU and GPU processing in simple terms.",
        "prompt_category": "short",
        "output_category": "long",
    },

    "long_prompt_short_output":
    {
        "name": "long_prompt_short_output",
        "num_predict": 32,
        "prompt": LONG_CONTEXT + "\n\nBased on the text above, answer in one sentence: what is the main topic?",
        "prompt_category": "long",
        "output_category": "short",
    },

    "long_prompt_long_output":
    {
        "name": "long_prompt_long_output",
        "num_predict": 256,
        "prompt": LONG_CONTEXT + "\n\nSummarize the text above and explain its main implications.",
        "prompt_category": "long",
        "output_category": "long",
    },
}

