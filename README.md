# Criminal Behavior Detection System from Surveillance Cameras

This project is a full-stack solution for detecting criminal or abnormal behaviors from surveillance camera footage using deep learning, specifically the STEAD model. It includes:

- An AI model for anomaly detection using X3D features.
- Feature extraction code and training pipeline.
- A web-based dashboard for monitoring, reviewing, and managing detected activities.
- Integration with real-time camera streams.

---

### Pretrained models available in the saved_models folder

**Extracted X3D Features for UCF-Crime dataset**

[**UCF-Crime X3D Features on Google drive**](https://drive.google.com/file/d/1LBTddU2mKuWvpbFOrqylJrZQ4u-U-zxG/view?usp=sharing)  

Feature extraction code also available for modification  

#### Prepare the environment: 
        pip install -r requirements.txt
#### Test: Run 
        python test.py
#### Train: Modify the option.py and run 
        python main.py


## Citation
    @misc{gao2025steadspatiotemporalefficientanomaly,
          title={STEAD: Spatio-Temporal Efficient Anomaly Detection for Time and Compute Sensitive Applications}, 
          author={Andrew Gao and Jun Liu},
          year={2025},
          eprint={2503.07942},
          archivePrefix={arXiv},
          primaryClass={cs.CV},
          url={https://arxiv.org/abs/2503.07942}, 
    }
