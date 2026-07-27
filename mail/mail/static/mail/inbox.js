let currentMailbox = 'inbox';


document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);
  document.querySelector('#compose-form').addEventListener('submit', submit_compose);

  // By default, load the inbox
  load_mailbox('inbox');
});

function compose_email() {
  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';
}

function submit_compose(event) {
  event.preventDefault();

  const recipients = document.querySelector('#compose-recipients').value;
  const subject = document.querySelector('#compose-subject').value;
  const body = document.querySelector('#compose-body').value;

  fetch('/emails', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipients, subject, body })
  })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      if (!ok) {
        throw new Error(data.error || 'Unable to send email.');
      }
      load_mailbox('sent');
    })
    .catch(error => {
      alert(error.message);
      console.error(error);
    });
}

function load_mailbox(mailbox) {
  currentMailbox = mailbox;

  // Show the mailbox and hide other views
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  const emailsView = document.querySelector('#emails-view');
  emailsView.innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3><div id="mailbox-list"></div>`;

  fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {
      const mailboxList = document.querySelector('#mailbox-list');

      if (!emails.length) {
        mailboxList.innerHTML = '<p>No emails in this mailbox.</p>';
        return;
      }

      emails.forEach(email => {
        const emailBox = document.createElement('div');
        emailBox.style.border = '1px solid #ccc';
        emailBox.style.padding = '10px';
        emailBox.style.marginBottom = '10px';
        emailBox.style.backgroundColor = email.read ? '#e5e5e5' : '#ffffff';
        emailBox.style.cursor = 'pointer';

        emailBox.innerHTML = `
          <strong>${escapeHtml(email.sender)}</strong><br>
          <span>${escapeHtml(email.subject || '(No subject)')}</span><br>
          <small>${escapeHtml(email.timestamp)}</small>
        `;

        emailBox.addEventListener('click', () => view_email(email.id));
        mailboxList.appendChild(emailBox);
      });
    })
    .catch(error => {
      emailsView.innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3><p>Unable to load mailbox.</p>`;
      console.error(error);
    });
}

function view_email(emailId) {
  fetch(`/emails/${emailId}`)
    .then(response => response.json())
    .then(email => {
      if (email.error) {
        throw new Error(email.error);
      }

      return fetch(`/emails/${emailId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ read: true })
      }).then(() => email);
    })
    .then(email => {
      render_email_view(email);
    })
    .catch(error => {
      alert(error.message);
      console.error(error);
    });
}

function render_email_view(email) {
  const emailsView = document.querySelector('#emails-view');
  emailsView.style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  let actionButtons = '';

  if (currentMailbox === 'inbox' && !email.archived) {
    actionButtons += `<button class="btn btn-sm btn-outline-secondary" id="archive-btn">Archive</button>`;
  } else if (currentMailbox === 'archive') {
    actionButtons += `<button class="btn btn-sm btn-outline-secondary" id="unarchive-btn">Unarchive</button>`;
  }

  actionButtons += ` <button class="btn btn-sm btn-outline-primary" id="reply-btn">Reply</button>`;

  emailsView.innerHTML = `
    <h3>${escapeHtml(email.subject || '(No subject)')}</h3>
    <p><strong>From:</strong> ${escapeHtml(email.sender)}</p>
    <p><strong>To:</strong> ${escapeHtml(email.recipients.join(', '))}</p>
    <p><strong>Timestamp:</strong> ${escapeHtml(email.timestamp)}</p>
    <div style="white-space: pre-wrap; margin-bottom: 12px;">${escapeHtml(email.body)}</div>
    <div>${actionButtons}</div>
  `;

  if (currentMailbox === 'inbox' && !email.archived) {
    document.querySelector('#archive-btn').addEventListener('click', () => archive_email(email.id));
  } else if (currentMailbox === 'archive') {
    document.querySelector('#unarchive-btn').addEventListener('click', () => unarchive_email(email.id));
  }

  document.querySelector('#reply-btn').addEventListener('click', () => reply_email(email));
}

function archive_email(emailId) {
  fetch(`/emails/${emailId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ archived: true })
  })
    .then(() => load_mailbox('inbox'))
    .catch(error => {
      alert('Unable to archive email.');
      console.error(error);
    });
}

function unarchive_email(emailId) {
  fetch(`/emails/${emailId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ archived: false })
  })
    .then(() => load_mailbox('inbox'))
    .catch(error => {
      alert('Unable to unarchive email.');
      console.error(error);
    });
}

function reply_email(email) {
  compose_email();

  const subject = email.subject.startsWith('Re: ') ? email.subject : `Re: ${email.subject}`;
  const body = `On ${email.timestamp}, ${email.sender} wrote:\n\n${email.body}`;

  document.querySelector('#compose-recipients').value = email.sender;
  document.querySelector('#compose-subject').value = subject;
  document.querySelector('#compose-body').value = body;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}