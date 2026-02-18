<script setup>
import { computed } from 'vue'

const props = defineProps({
    show: {
        type: Boolean,
        default: false
    },
    result: {
        type: Object,
        default: null
    },
    loading: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['close'])

const isSuccess = computed(() => props.result?.success ?? false)

const formatTime = (isoString) => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}

const closeModal = () => {
    emit('close')
}

const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
        closeModal()
    }
}
</script>

<template>
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="show" class="modal-overlay" @click="handleBackdropClick">
                <div class="modal-container">
                    <!-- Loading State -->
                    <div v-if="loading" class="modal-content loading">
                        <div class="loading-spinner">
                            <svg class="spinner" xmlns="http://www.w3.org/2000/svg" width="48" height="48"
                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                            </svg>
                        </div>
                        <p class="loading-text">명령을 전송 중입니다...</p>
                    </div>

                    <!-- Result State -->
                    <div v-else class="modal-content">
                        <div class="result-icon" :class="{ success: isSuccess, error: !isSuccess }">
                            <!-- Success Icon -->
                            <svg v-if="isSuccess" xmlns="http://www.w3.org/2000/svg" width="48" height="48"
                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                stroke-linecap="round" stroke-linejoin="round">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                <polyline points="22 4 12 14.01 9 11.01" />
                            </svg>
                            <!-- Error Icon -->
                            <svg v-else xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="15" y1="9" x2="9" y2="15" />
                                <line x1="9" y1="9" x2="15" y2="15" />
                            </svg>
                        </div>

                        <h3 class="result-title" :class="{ success: isSuccess, error: !isSuccess }">
                            {{ isSuccess ? '전송 완료' : '전송 실패' }}
                        </h3>

                        <p class="result-message">{{ result?.message || '결과를 불러올 수 없습니다.' }}</p>

                        <div class="result-details" v-if="result">
                            <div class="detail-row" v-if="result.boxCount">
                                <span class="detail-label">박스 개수</span>
                                <span class="detail-value">{{ result.boxCount }}개</span>
                            </div>
                            <div class="detail-row" v-if="result.sentAt">
                                <span class="detail-label">전송 시간</span>
                                <span class="detail-value">{{ formatTime(result.sentAt) }}</span>
                            </div>
                            <div class="detail-row" v-if="result.commandId">
                                <span class="detail-label">명령 ID</span>
                                <span class="detail-value mono">{{ result.commandId }}</span>
                            </div>
                        </div>

                        <button class="btn-close" @click="closeModal">
                            확인
                        </button>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 20px;
}

.modal-container {
    background: var(--glass-panel);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
    max-width: 380px;
    width: 100%;
    overflow: hidden;
}

.modal-content {
    padding: 32px 28px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.modal-content.loading {
    padding: 48px 28px;
}

/* Loading State */
.loading-spinner {
    margin-bottom: 16px;
    color: var(--color-primary);
}

.spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}

.loading-text {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0;
}

/* Result State */
.result-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
}

.result-icon.success {
    background: rgba(16, 185, 129, 0.15);
    color: var(--color-success);
}

.result-icon.error {
    background: rgba(239, 68, 68, 0.15);
    color: var(--color-error);
}

.result-title {
    font-size: 22px;
    font-weight: 700;
    margin: 0 0 8px 0;
}

.result-title.success {
    color: var(--color-success);
}

.result-title.error {
    color: var(--color-error);
}

.result-message {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0 0 24px 0;
    line-height: 1.5;
}

.result-details {
    width: 100%;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
}

.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
}

.detail-row:not(:last-child) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.detail-value {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
}

.detail-value.mono {
    font-family: var(--font-family-mono);
    font-size: 11px;
}

.btn-close {
    width: 100%;
    padding: 14px 24px;
    background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark, #4f46e5));
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 4px 12px var(--color-primary-glow);
}

.btn-close:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px var(--color-primary-glow);
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
    transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
    transform: scale(0.9) translateY(20px);
}

.modal-enter-to .modal-container,
.modal-leave-from .modal-container {
    transform: scale(1) translateY(0);
}

@media (max-width: 480px) {
    .modal-container {
        max-width: 100%;
        margin: 0 10px;
    }

    .modal-content {
        padding: 24px 20px;
    }

    .result-icon {
        width: 64px;
        height: 64px;
    }

    .result-icon svg {
        width: 36px;
        height: 36px;
    }

    .result-title {
        font-size: 18px;
    }
}
</style>
