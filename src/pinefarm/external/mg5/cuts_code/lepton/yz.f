c     cut on the rapidity of SFOS lepton pairs
      do i=1,nexternal-1
        if (is_a_lm_reco(i) .or. is_a_lp_reco(i)) then
          do j=i+1,nexternal
            if (ipdg(i) .eq. -ipdg(j)) then
              if (abs(atanh((p(3,i)+p(3,j))
     &            /(p(0,i)+p(0,j)))) .gt. {}) then
                passcuts_leptons=.false.
                return
              endif
            endif
          enddo
        endif
      enddo
