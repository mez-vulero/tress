import { createResource, call } from 'frappe-ui'
import { ref } from 'vue'

export const queueJoined = ref(false)
export const queueId = ref(null)

createResource({
  url: 'crm.integrations.websprix.api.queue_status',
  cache: 'Websprix Queue Status',
  auto: true,
  onSuccess(data) {
    queueJoined.value = Boolean(data?.joined)
    queueId.value = data?.queue_id || null
  },
})

export async function toggleQueue() {
  if (!queueId.value) return
  if (queueJoined.value) {
    await call('crm.integrations.websprix.api.leave_queue')
    queueJoined.value = false
  } else {
    await call('crm.integrations.websprix.api.join_queue')
    queueJoined.value = true
  }
}
