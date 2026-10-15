"""Assistant UI retains bounded question contexts; replies are re-rendered and recalculated."""
import hashlib
from .locale_ui import st, current, localized_frame
from .assistant import answer_question, render_parts, PROMPTS
from .risk import RiskPolicy


def assistant_view(t):
    data=st.session_state.get('active_data'); buyers=st.session_state.get('active_buyers')
    st.info(t('Rule-based assistant; no external model or live information is used.'))
    st.caption(t('Priority answers rank all active crops; scope applies to the other topics.'))
    if buyers is not None:
        origin=(st.session_state.get('buyers_metadata') or {}).get('origin')
        st.warning(t('Sample opportunities only; not confirmed orders' if origin=='sample' else 'Uploaded opportunities; not confirmed orders'))
    st.caption(t('Answers are recalculated from current active data and planning rules on every rerun.'))
    if data is None:
        st.info(t('Load validated agriculture data before asking the assistant.'));return
    fingerprint=hashlib.sha256(data.to_json().encode()).hexdigest()[:12]
    crop=st.selectbox(t('Assistant scope'),[None]+list(data.crop),format_func=lambda value:t('All crops') if value is None else t.entity(value,'Crop'),key=f'assistant_scope_{fingerprint}')
    suggestion=st.selectbox(t('Suggested question'),list(PROMPTS)[:-1],format_func=lambda intent:t(PROMPTS[intent]),key='assistant_suggestion')
    history=st.session_state.setdefault('assistant_questions',[])
    if st.button(t('Clear conversation'),key='clear_assistant'):
        history=[];st.session_state.assistant_questions=history
    if st.button(t('Use suggested question'),key='ask_suggestion'):
        history.append({'question':PROMPTS[suggestion],'crop':crop})
    if t.language=='தமிழ்':
        with st.form('assistant_tamil_form',clear_on_submit=True):
            question=st.text_area(t('Ask a question about the active data'),key='assistant_question_tamil',max_chars=2000,placeholder=t('Question'))
            send=st.form_submit_button(t('Ask'),key='send_assistant_tamil')
        if send and question.strip():history.append({'question':question,'crop':crop})
    else:
        question=st.chat_input(t('Ask a question about the active data'),key='assistant_chat',max_chars=2000)
        if question:history.append({'question':question,'crop':crop})
    st.session_state.assistant_questions=history[-20:]
    transcript=[]
    policy=RiskPolicy.from_dict(st.session_state.get('risk_policy'))
    for n,item in enumerate(st.session_state.assistant_questions,1):
        response=answer_question(item['question'],data,buyers,policy,item['crop'])
        # Display the recognized topic in the chosen language; the source question is kept internally.
        st.subheader(t('Question {n}',n=n))
        st.caption(t(PROMPTS[response.intent]))
        lines=render_parts(response,t)
        for line in lines:st.write(line)
        transcript.append(t('Question {n}',n=n)+'\n'+t(PROMPTS[response.intent])+'\n'+'\n'.join(lines))
        if not response.evidence.empty:
            with st.expander(t('Evidence from active calculations')):
                st.dataframe(response.evidence,hide_index=True,width='stretch')
        if response.sources:
            st.caption(t('Calculation sources')+': '+', '.join(t(source) for source in response.sources))
    if transcript:
        st.download_button(t('Download assistant conversation'),'\n\n'.join(transcript).encode(),file_name='assistant_conversation.txt',mime='text/plain')
    else:
        st.caption(t('No question yet'))
