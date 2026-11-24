"""Appended to a staged EDA runner; cloud CPU baselines without human labels."""


def run_cpu_baselines():
    # The EDA bootstrap unpacks the frozen workspace and sets source/env paths.
    main()
    install_offline_wheels()
    from fashion_reco.workflow import configure, build_retrievers, benchmark, environment
    from fashion_reco.inference import recommend
    from fashion_reco.data import dump_json
    config, products, manifest, requests, splits = configure(WORK/'source/configs/experiment.yaml')
    config['methods'] = ['tfidf','bm25']
    destination = WORK/'output/cpu-baseline'
    destination.mkdir(parents=True, exist_ok=True)
    config['output_dir'] = str(destination)
    retrievers = build_retrievers(config,products)
    validation = [q for q in requests if q.query_id in set(splits['validation'])]
    latency = benchmark(validation,products,retrievers)
    bundles = []
    for request in validation[:6]:
        for method in retrievers:
            for mode in ('research','available_only'):
                result = recommend(request,products,{'retrievers':retrievers,'ranker':None},
                                   method=method,mode=mode)
                bundles.append({'query_id':request.query_id,'query':request.text,
                                'method':method,'mode':mode,**result})
    dump_json(destination/'bundles-preview.json',bundles)
    summary = {'status':'cpu_baselines_complete','catalog_count':len(products),
               'catalog_sha256':manifest['sha256'],'methods':list(retrievers),
               'benchmark_queries':len(validation),'latency':latency,
               'quality_metrics':None,
               'note':'Preliminary cloud CPU run. No relevance labels, no NDCG or best-model claim. E5/BGE candidate pool is unchanged.'}
    dump_json(destination/'summary.json',summary)
    dump_json(destination/'environment.json',environment())
    print(summary,flush=True)


if __name__ == '__main__':
    run_cpu_baselines()
