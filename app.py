from starlette.applications import Starlette
from starlette.responses import UJSONResponse
import gpt_2_simple as gpt2
import tensorflow as tf
import uvicorn
import os
import gc

app = Starlette(debug=False)

sess = gpt2.start_tf_sess(threads=1)
gpt2.load_gpt2(sess)

# Needed to avoid cross-domain issues
response_header = {
    'Access-Control-Allow-Origin': '*'
}

generate_count = 0


@app.route('/', methods=['GET', 'POST', 'HEAD'])
async def homepage(request):
    global generate_count
    global sess

    if request.method == 'GET':
        params = request.query_params
    elif request.method == 'POST':
        params = await request.json()
    elif request.method == 'HEAD':
        return UJSONResponse({'text': ''},
                             headers=response_header)

    text = gpt2.generate(sess,
                         length=55,
                         temperature=float(params.get('temperature', 0.9)),
                         top_k=int(params.get('top_k', 0)),
                         top_p=float(params.get('top_p', 0)),
                         prefix= '<|startoftext|>' + params.get('prefix', '')[:500],
                         truncate='<|endoftext|>',
                         include_prefix=True,
                         return_as_list=True,
                         nsamples=int(params.get('nsamples',1))
                         )[0]

    #for x in text:
      #  x = x.replace('<|startoftext|>', '')
       # x = x.replace('<|endoftext|>', '')
       # x = x.replace('\n', '')
        #x = x.replace('  ', ' ')

    generate_count += 1
    if generate_count == 8:
        # Reload model to prevent Graph/Session from going OOM
        tf.reset_default_graph()
        sess.close()
        sess = gpt2.start_tf_sess(threads=1)
        gpt2.load_gpt2(sess)
        generate_count = 0

    gc.collect()
    return UJSONResponse({'text': text},
                         headers=response_header)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))