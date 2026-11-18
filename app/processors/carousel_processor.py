async def process(paths, extractor):
    images=[open(p,'rb').read() for p in paths]; prompt='Carousel slides in order. Analyze all slides as one coherent source.\n'
    return await extractor.analyze(prompt, images)
