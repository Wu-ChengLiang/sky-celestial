import React from 'react';
import styles from '@/styles/DonationModal.module.css';

interface DonationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DonationModal: React.FC<DonationModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeButton} onClick={onClose}>×</button>
        <h2>¥5.20</h2>
        <p>感谢你的支持 Thanks for donating</p>
        <div className={styles.qrCodeContainer}>
          <img src="/images/donating.jpg" alt="Donation QR Code" className={styles.qrCode} />
        </div>
      </div>
    </div>
  );
};

export default DonationModal; 