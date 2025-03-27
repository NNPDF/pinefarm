c     cut on the minimum pseudorapidity of leptons
      do i=1,nexternal-1
        if (is_a_lm_reco(i) .or. is_a_lp_reco(i)) then
          if (abs(atanh(p(3,i)/sqrt(p(1,i)**2+p(2,i)**2+
     &                  p(3,i)**2))) .lt. {}) then
            passcuts_leptons=.false.
            return
          endif
        endif
      enddo
