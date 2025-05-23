class ConsecutiveDetector:
    """
    Class de phat hien pham phap dua tren so batch vuong nguong 
    """
    def __init__(self, threshold, consecutive_required):
        """
        Args:
            threshold : nguong xac dinh
            consecutive_required : so batch can thiet de canh bao
        """
        self.threshold = threshold
        self.consecutive_required = consecutive_required
        self.consecutive_count = 0
        self.last_batch_idx = -1
        self.anomaly_detected = False
        self.recent_results = []  
        self.total_processed = 0
        print(f" ConsecutiveDetector initialized: threshold={threshold}, required={consecutive_required}")
        
    def update(self, batch_idx, prob):
        
        self.total_processed += 1
        print(f" Processing Batch {batch_idx}: Prob {prob:.4f} (Threshold: {self.threshold})")
        
   
        if self.last_batch_idx == -1 or batch_idx == self.last_batch_idx + 1:
       
            if prob > self.threshold:
                self.consecutive_count += 1
                print(f" Above threshold! Consecutive: {self.consecutive_count}/{self.consecutive_required}")
            else:
           
                if self.consecutive_count > 0:
                    print(f" Below threshold - Reset consecutive count (was {self.consecutive_count})")
                self.consecutive_count = 0
             
                if len(self.recent_results) >= 2 and all(r <= self.threshold for r in self.recent_results[-2:]):
                    if self.anomaly_detected:
                        print(f" Anomaly status reset to normal")
                    self.anomaly_detected = False
        else:
          
            print(f" Non-consecutive batch (last: {self.last_batch_idx}, current: {batch_idx}) - Resetting")
            self.consecutive_count = 0 if prob <= self.threshold else 1
            self.anomaly_detected = False
            
       
        if self.consecutive_count >= self.consecutive_required:
            if not self.anomaly_detected:
                print(f" ANOMALY DETECTED: {self.consecutive_required} consecutive batches exceed threshold!")
            self.anomaly_detected = True
        
       
        self.recent_results.append(prob)
        if len(self.recent_results) > 10:
            self.recent_results.pop(0)
            
        self.last_batch_idx = batch_idx
        print(f" Current state: consecutive={self.consecutive_count}, anomaly={self.anomaly_detected}")
        
    def get_status(self):
       
        return self.anomaly_detected, self.consecutive_count
    
    def get_detailed_status(self):
        
        return {
            'anomaly_detected': self.anomaly_detected,
            'consecutive_count': self.consecutive_count,
            'consecutive_required': self.consecutive_required,
            'threshold': self.threshold,
            'last_batch_idx': self.last_batch_idx,
            'total_processed': self.total_processed,
            'recent_results': self.recent_results.copy()
        }
    
    def reset(self):
        
        print(" Resetting ConsecutiveDetector")
        self.consecutive_count = 0
        self.last_batch_idx = -1
        self.anomaly_detected = False
        self.recent_results.clear()
        self.total_processed = 0
    
    def set_threshold(self, new_threshold):
        
        old_threshold = self.threshold
        self.threshold = new_threshold
        print(f" Threshold changed: {old_threshold} -> {new_threshold}")
    
    def set_consecutive_required(self, new_required):
        
        old_required = self.consecutive_required
        self.consecutive_required = new_required
        print(f" Consecutive required changed: {old_required} -> {new_required}")